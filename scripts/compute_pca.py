#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM 2018
#  Author: Xavier Corredor Llano <xcorredorl@ideam.gov.co>
#
import click
import numpy as np
from pathlib import Path
import dask
from multiprocessing import cpu_count
from osgeo import gdal
from dask import array as da
from multiprocessing.pool import ThreadPool
from subprocess import call


@click.command()
@click.option('--A', type=click.Path(exists=True, readable=True), required=True)
@click.option('--B', type=click.Path(exists=True, readable=True))
@click.option('--n-pc', type=click.INT, required=True)
@click.option('--estimator-matrix', type=click.Choice(["correlation", "covariance"]), default="correlation")
@click.option('--out-dir', type=click.Path(exists=True, readable=True), default=".")
@click.option('--n-threads', type=click.INT, default=cpu_count())
@click.option('--block-size', type=click.INT, default=1000)
@click.option('--nodata', type=click.INT, default=None)
def pca(a, b, n_pc, estimator_matrix, out_dir, n_threads, block_size, nodata):
    """Calculate the principal components for the vertical stack A or with
    combinations of the stack B

    :param A: first input raster data (fists period)
    :param B: second input raster data (second period) or None
    :param n_pc: number of principal components to output
    :param estimator_matrix: pca with correlation of covariance
    :param out_dir: directory to save the outputs
    :return: pca files list and statistics
    """
    A = a
    B = b
    # get/set the nodata
    if nodata is None:
        ds = gdal.Open(A, gdal.GA_ReadOnly)
        nodata = ds.GetRasterBand(1).GetNoDataValue()
        del ds

    # init dask as threads (shared memory is required)
    dask.config.set(pool=ThreadPool(n_threads))

    raw_image = []
    nodata_mask = None
    src_ds_A = gdal.Open(A, gdal.GA_ReadOnly)
    src_ds_B = None
    for band in range(src_ds_A.RasterCount):
        ds = src_ds_A.GetRasterBand(band + 1).ReadAsArray().flatten().astype(np.float32)
        if nodata is not None:
            nodata_mask = ds==nodata if nodata_mask is None else np.logical_or(nodata_mask, ds==nodata)
        raw_image.append(ds)
    if B is not None:
        src_ds_B = gdal.Open(B, gdal.GA_ReadOnly)
        for band in range(src_ds_B.RasterCount):
            ds = src_ds_B.GetRasterBand(band + 1).ReadAsArray().flatten().astype(np.float32)
            if nodata is not None:
                nodata_mask = np.logical_or(nodata_mask, ds==nodata)
            raw_image.append(ds)

    # pair-masking data, let only the valid data across all dimensions/bands
    if nodata is not None:
        raw_image = [b[~nodata_mask] for b in raw_image]
    # flat each dimension (bands)
    flat_dims = da.vstack(raw_image).rechunk((1, block_size ** 2))
    # bands
    n_bands = flat_dims.shape[0]

    ########
    # compute the mean of each band, in order to center the matrix.
    band_mean = []
    for i in range(n_bands):
        band_mean.append(dask.delayed(np.mean)(flat_dims[i]))
    band_mean = dask.compute(*band_mean)

    ########
    # compute the matrix correlation/covariance
    estimation_matrix = np.empty((n_bands, n_bands))
    if estimator_matrix == "correlation":
        for i in range(n_bands):
            deviation_scores_band_i = flat_dims[i] - band_mean[i]
            for j in range(i, n_bands):
                deviation_scores_band_j = flat_dims[j] - band_mean[j]
                estimation_matrix[j][i] = estimation_matrix[i][j] = \
                    da.corrcoef(deviation_scores_band_i, deviation_scores_band_j)[0][1]
    if estimator_matrix == "covariance":
        for i in range(n_bands):
            deviation_scores_band_i = flat_dims[i] - band_mean[i]
            for j in range(i, n_bands):
                deviation_scores_band_j = flat_dims[j] - band_mean[j]
                estimation_matrix[j][i] = estimation_matrix[i][j] = \
                    da.cov(deviation_scores_band_i, deviation_scores_band_j)[0][1]
    # free mem
    del raw_image, flat_dims, src_ds_B, ds

    ########
    # calculate eigenvectors & eigenvalues of the matrix
    # use 'eigh' rather than 'eig' since estimation_matrix
    # is symmetric, the performance gain is substantial
    eigenvals, eigenvectors = np.linalg.eigh(estimation_matrix)

    # sort eigenvalue in decreasing order
    idx_eigenvals = np.argsort(eigenvals)[::-1]
    eigenvectors = eigenvectors[:,idx_eigenvals]
    # sort eigenvectors according to same index
    eigenvals = eigenvals[idx_eigenvals]
    # select the first n eigenvectors (n is desired dimension
    # of rescaled data array, or dims_rescaled_data)
    eigenvectors = eigenvectors[:, :n_pc]

    ########
    # save the principal components separated in tif images

    def get_raw_band_from_stack(band):
        src_ds_A = gdal.Open(A, gdal.GA_ReadOnly)
        if band < src_ds_A.RasterCount:
            return src_ds_A.GetRasterBand(band + 1).ReadAsArray().flatten().astype(np.float32)
        if band >= src_ds_A.RasterCount:
            src_ds_B = gdal.Open(B, gdal.GA_ReadOnly)
            return src_ds_B.GetRasterBand(band - src_ds_A.RasterCount + 1).ReadAsArray().flatten().astype(np.float32)

    @dask.delayed
    def get_principal_component(i, j):
        return eigenvectors[j, i] * (get_raw_band_from_stack(j) - band_mean[j])

    pca_files = []
    for i in range(n_pc):
        pc = dask.delayed(sum)([get_principal_component(i, j) for j in range(n_bands)])
        pc = pc.astype(np.float32)
        pc = np.array(pc.compute())
        if nodata is not None:
            pc[nodata_mask] = 0
        pc = pc.reshape((src_ds_A.RasterYSize, src_ds_A.RasterXSize))
        # save component as file
        tmp_pca_file = Path(out_dir) / 'pc_{}.tif'.format(i+1)
        driver = gdal.GetDriverByName("GTiff")
        out_pc = driver.Create(str(tmp_pca_file), src_ds_A.RasterXSize, src_ds_A.RasterYSize, 1, gdal.GDT_Float32)
        pcband = out_pc.GetRasterBand(1)
        if nodata is not None:
            pcband.SetNoDataValue(0)
        pcband.WriteArray(pc)
        # set projection and geotransform
        if src_ds_A.GetGeoTransform() is not None:
            out_pc.SetGeoTransform(src_ds_A.GetGeoTransform())
        if src_ds_A.GetProjection() is not None:
            out_pc.SetProjection(src_ds_A.GetProjection())
        out_pc.FlushCache()
        del pc, pcband, out_pc

        pca_files.append(tmp_pca_file)

    # free mem
    del src_ds_A, nodata_mask

    # compute the pyramids for each pc image
    @dask.delayed
    def pyramids(pca_file):
        call("gdaladdo -q --config BIGTIFF_OVERVIEW YES {}".format(pca_file), shell=True)

    dask.compute(*[pyramids(pca_file) for pca_file in pca_files], num_workers=2)


if __name__ == '__main__':
    pca()
