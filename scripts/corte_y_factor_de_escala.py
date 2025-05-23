#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2022 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
# Realiza el corte al area efectiva, reproyecta y aplica
# el factor de escala para la coleccion 2 de Landsat
#
import glob
import os
import argparse
import platform
import subprocess

from osgeo import gdal

gdal.UseExceptions()
gdal.PushErrorHandler('CPLQuietErrorHandler')


def check_zero_pixel(img_file):
    """Convert the pixels in the band if at least there is one pixel in other bands as zero"""
    ds = gdal.Open(img_file, gdal.GA_Update)

    bands = ds.RasterCount
    for band in range(1, bands + 1):
        band_ds = ds.GetRasterBand(band)
        data = band_ds.ReadAsArray()

        if band == 1:
            mask = data == 0
        else:
            mask = mask | (data == 0)

    # apply mask to all bands
    for band in range(1, bands + 1):
        band_ds = ds.GetRasterBand(band)
        data = band_ds.ReadAsArray()
        data[mask] = 0
        band_ds.WriteArray(data)

    ds = None


def script():
    """Run as a script with arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('inputs', type=str, help='directories and/or files', nargs='*')
    parser.add_argument('--apply-factor', action='store_true', help='apply the factor for Landsat Collection 2', default=False)
    parser.add_argument('--cut-area-shapefile', type=str, help='shapefile path for cut the area', default=None)

    args = parser.parse_args()

    if args.apply_factor:
        print("\nApply scale factor for collection 2: ENABLED")
    else:
        print("\nApply scale factor for collection 2: DISABLED")

    # search all Image files in inputs recursively if the files are in directories
    img_files = []
    for _input in args.inputs:
        if os.path.isfile(_input):
            if _input.endswith(('.tif', '.TIF')):
                img_files.append(os.path.abspath(_input))
        elif os.path.isdir(_input):
            for root, dirs, files in os.walk(_input):
                if len(files) != 0:
                    files = [os.path.join(root, x) for x in files if x.endswith(('.tif', '.TIF'))]
                    [img_files.append(os.path.abspath(file)) for file in files]

    # process
    print("\nIMAGES TO PROCESS: {}\n".format(len(img_files)))
    out_dir = "corte_y_factor"
    os.makedirs(out_dir, exist_ok=True)

    for img_file in img_files:
        print("PROCESSING: " + os.path.basename(img_file))

        path_row = os.path.basename(img_file).split("_")
        path_row = path_row[1] + "_" + path_row[2]

        final_file = os.path.join(os.path.dirname(img_file), out_dir, os.path.basename(img_file))

        if args.cut_area_shapefile is None:
            path_to_cut_file = os.path.join("/home/smbyc/cona2/Imagenes/Landsat/6.3.Area_Efectiva/", path_row)
            cut_area_file = glob.glob(os.path.join(path_to_cut_file, "*.shp"))
            if cut_area_file:
                if len(cut_area_file) > 1:
                    cut_area_shapefile = [f for f in cut_area_file if f.endswith("Z18N.shp")][0]
                    if not cut_area_shapefile:
                        print("\tERROR: No se pudo definir cual es el archivo del area efectiva en: {}".format(path_to_cut_file))
                        return
                else:
                    cut_area_shapefile = cut_area_file[0]
            else:
                cut_area_shapefile = path_to_cut_file
        else:
            cut_area_shapefile = args.cut_area_shapefile

        if not os.path.isfile(cut_area_shapefile):
            print("\tERROR: No se encontro el shapefile para el area efectiva: {}".format(cut_area_shapefile))
            return

        # clip avg image with cut area shapefile
        avg_image = "/home/smbyc/cona2/Imagenes/Landsat/Average_25_75/AV2575_C2_2000_2021_v1.tif"
        avg_clip_file = os.path.join(os.path.dirname(img_file), out_dir, "{random}.tif".format(random=os.urandom(4).hex()))
        gdal.Warp(avg_clip_file, avg_image, cutlineDSName=cut_area_shapefile, cropToCutline=True, multithread=True, outputType=gdal.GDT_Byte)

        # get avg image extent
        avg_ds = gdal.Open(avg_clip_file)
        geoTransform = avg_ds.GetGeoTransform()
        minx = geoTransform[0]
        maxy = geoTransform[3]
        maxx = minx + geoTransform[1] * avg_ds.RasterXSize
        miny = maxy + geoTransform[5] * avg_ds.RasterYSize
        avg_clip_extent = [minx, miny, maxx, maxy]
        avg_ds = None
        if os.path.isfile(avg_clip_file):
            os.remove(avg_clip_file)
        if os.path.isfile(avg_clip_file + ".aux.xml"):
            os.remove(avg_clip_file + ".aux.xml")

        if args.apply_factor:
            print("\tApplying factor to the image")
            tmp_file = os.path.join(os.path.dirname(img_file), out_dir, "{random}.tif".format(random=os.urandom(4).hex()))
            cmd = ['gdal_calc' if platform.system() == 'Windows' else 'gdal_calc.py', '--overwrite',
                   '--calc', '"((A*0.0000275)-0.2)*10000"', "--quiet", "--allBands A",
                   '--outfile', '"{}"'.format(tmp_file), '--format', 'GTiff',
                   "-A", '"{}"'.format(img_file)]
            subprocess.run(" ".join(cmd), shell=True)
            img_file = tmp_file

        gdal.Warp(final_file, img_file, dstSRS='EPSG:32618', xRes=30, yRes=30, cutlineDSName=cut_area_shapefile,
                  outputBounds=avg_clip_extent, resampleAlg=gdal.gdalconst.GRA_NearestNeighbour, multithread=True,
                  dstNodata=0, outputType=gdal.gdalconst.GDT_UInt16)

        # check if there is zero pixel in the final image
        print("\tChecking zero pixel in the final image")
        check_zero_pixel(final_file)

        # remove temporary file
        if args.apply_factor:
            os.remove(tmp_file)
    print("\nDONE")

if __name__ == '__main__':
    script()