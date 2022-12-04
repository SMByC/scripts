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

import fiona
from osgeo import gdal

gdal.UseExceptions()
gdal.PushErrorHandler('CPLQuietErrorHandler')


def script():
    """Run as a script with arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('inputs', type=str, help='directories and/or files', nargs='*')
    args = parser.parse_args()

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

    for target_file in img_files:
        print("PROCESSING: " + os.path.basename(target_file))

        # mask file
        path_row = os.path.basename(target_file).split("_")
        path_row = path_row[1] + "_" + path_row[2]
        path_row_date = "_".join(os.path.basename(target_file).split("_")[0:4])
        mask_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(target_file)))))
        # first file in dir that start with pattern: "LC08_L1TP_"
        mask_file = glob.glob(os.path.join(mask_dir, "{}*".format(path_row_date)))[0]

        final_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(target_file))),
                                 "3.2.2.Reflectancia_SR_Enmascarada", path_row)
        os.makedirs(final_dir, exist_ok=True)
        final_file = os.path.join(final_dir, os.path.basename(target_file).replace("_Reflec", "_Reflec_SR_Enmask"))

        if not os.path.isfile(mask_file):
            print("ERROR: mask file not found: {}".format(mask_file))
            return

        # get target image extent
        gdal_ds = gdal.Open(target_file)
        geoTransform = gdal_ds.GetGeoTransform()
        minx = geoTransform[0]
        maxy = geoTransform[3]
        maxx = minx + geoTransform[1] * gdal_ds.RasterXSize
        miny = maxy + geoTransform[5] * gdal_ds.RasterYSize
        target_extent = [minx, miny, maxx, maxy]
        gdal_ds = None

        tmp_file = os.path.join(os.path.dirname(final_file), "{random}.tif".format(random=os.urandom(4).hex()))

        cmd = ['gdalwarp.exe' if platform.system() == 'Windows' else 'gdalwarp',
               '-te {} {} {} {}'.format(*target_extent), '-overwrite', '-of', 'GTiff', "-q",
               '"{}"'.format(mask_file), '"{}"'.format(tmp_file)]
        subprocess.run(" ".join(cmd), shell=True)

        cmd = ['gdal_calc' if platform.system() == 'Windows' else 'gdal_calc.py', "--quiet", "--allBands A",
               '--calc="A*(B==1)+0*(B!=1)"', '--overwrite',
               '-A "{}" -B "{}" --outfile="{}"'.format(target_file, tmp_file, final_file)]
        subprocess.run(" ".join(cmd), shell=True)
        os.remove(tmp_file)

    print("\nDONE")


if __name__ == '__main__':
    script()