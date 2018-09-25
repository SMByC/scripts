#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2016-2018 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
from __future__ import print_function
from __future__ import unicode_literals

import os, sys
import argparse
import shutil

# add project dir to pythonpath
libs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "libs")
if libs_dir not in sys.path:
    sys.path.append(libs_dir)

import gdal_merge, gdal_calc
from fmask import fmask, landsatTOA, landsatangles, config, saturationcheck
from rios import fileinfo


def script():
    """Run as a script with arguments
    """
    parser = argparse.ArgumentParser(
        prog='cloud-masking-bulk',
        description='Compute and generate the cloud mask (fmask) for all Landsat input')

    parser.add_argument('--cloud-prob-thresh', type=float, default=0.225, required=False)
    parser.add_argument('--cloud_buffer_size', type=int, default=4, required=False)
    parser.add_argument('--shadow_buffer_size', type=int, default=6, required=False)
    parser.add_argument('--cirrus_prob_ratio', type=float, default=0.04, required=False)
    parser.add_argument('--nir_fill_thresh', type=float, default=0.02, required=False)
    parser.add_argument('--swir2_thresh', type=float, default=0.03, required=False)
    parser.add_argument('--whiteness_thresh', type=float, default=0.7, required=False)
    parser.add_argument('--swir2_water_test', type=float, default=0.03, required=False)
    parser.add_argument('--nir_snow_thresh', type=float, default=0.11, required=False)
    parser.add_argument('--green_snow_thresh', type=float, default=0.1, required=False)
    parser.add_argument('--blue_band_l457', type=int, default=-1, required=False)
    parser.add_argument('--blue_band_l8', type=int, default=-1, required=False)

    parser.add_argument('inputs', type=str, help='directories or MTL files to process', nargs='*')

    args = parser.parse_args()

    print("\nLoading the MTL files: ", end="")
    # search all Image files in inputs recursively if the files are in directories
    mtl_files = []
    for _input in args.inputs:
        if os.path.isfile(_input):
            if _input.endswith("_MTL.txt"):
                mtl_files.append(os.path.abspath(_input))
        elif os.path.isdir(_input):
            for root, dirs, files in os.walk(_input):
                if len(files) != 0:
                    files = [os.path.join(root, x) for x in files if x.endswith("_MTL.txt")]
                    [mtl_files.append(os.path.abspath(file)) for file in files]
    print("{} Landsat files to process\n".format(len(mtl_files)))

    filters_enabled = {"Fmask Cloud": True, "Fmask Shadow": True, "Fmask Snow": True, "Fmask Water": False}

    for mtl_file in mtl_files:
        print("PROCESSING: " + os.path.basename(mtl_file).split("_MTL.txt")[0])
        cloud_masking_files = []

        tmp_dir = os.path.join(os.path.dirname(mtl_file), "tmp_dir")
        if not os.path.isdir(tmp_dir):
            os.makedirs(tmp_dir)

        cloud_masking_files.append(
            do_fmask(mtl_file, filters_enabled, tmp_dir, 0, args.cloud_prob_thresh, args.cloud_buffer_size,
                     args.shadow_buffer_size, args.cirrus_prob_ratio, args.nir_fill_thresh, args.swir2_thresh,
                     args.whiteness_thresh, args.swir2_water_test, args.nir_snow_thresh, args.green_snow_thresh))

        cloud_masking_files.append(do_blue_band(mtl_file, args.blue_band_l457, args.blue_band_l8, tmp_dir))

        cloud_masking_files = [i for i in cloud_masking_files if i is not None]

        cloud_mask_file = mtl_file.split("_MTL.txt")[0] + "_mask.tif"


        if len(cloud_masking_files) == 1:
            gdal_calc.Calc(calc="0*(A==1)+3*(A!=1)", outfile=cloud_mask_file,
                           A=cloud_masking_files[0])

        if len(cloud_masking_files) == 2:
            gdal_calc.Calc(calc="0*logical_and(A==1,B==1)+3*logical_or(A!=1,B!=1)",
                           outfile=cloud_mask_file,
                           A=cloud_masking_files[0], B=cloud_masking_files[1])

        shutil.rmtree(tmp_dir, ignore_errors=True)

        ### ending fmask process
        print("DONE\n")


def do_fmask(mtl_file, filters_enabled, tmp_dir, min_cloud_size=0, cloud_prob_thresh=0.225, cloud_buffer_size=4,
             shadow_buffer_size=6, cirrus_prob_ratio=0.04, nir_fill_thresh=0.02, swir2_thresh=0.03,
             whiteness_thresh=0.7, swir2_water_test=0.03, nir_snow_thresh=0.11, green_snow_thresh=0.1):

    print("Fmask:")

    input_dir = os.path.dirname(mtl_file)

    # parser
    mtl_file_parse = mtl2dict(mtl_file)

    # get the landsat version
    landsat_version = int(mtl_file_parse['SPACECRAFT_ID'][-1])

    # set bands for reflective and thermal
    if landsat_version in [4, 5]:
        # get the reflective file names bands
        reflective_bands = [
            os.path.join(input_dir, mtl_file_parse['FILE_NAME_BAND_' + str(N)])
            for N in [1, 2, 3, 4, 5, 7]]
        # get the thermal file names bands
        thermal_bands = [
            os.path.join(input_dir, mtl_file_parse['FILE_NAME_BAND_' + str(N)])
            for N in [6]]

    # set bands for reflective and thermal
    if landsat_version == 7:
        # get the reflective file names bands
        reflective_bands = [
            os.path.join(input_dir, mtl_file_parse['FILE_NAME_BAND_' + str(N)])
            for N in [1, 2, 3, 4, 5, 7]]
        # get the thermal file names bands
        thermal_bands = [
            os.path.join(input_dir, mtl_file_parse['FILE_NAME_BAND_6_VCID_' + str(N)])
            for N in [1, 2]]

    # set bands for reflective and thermal
    if landsat_version == 8:
        # get the reflective file names bands
        reflective_bands = [
            os.path.join(input_dir, mtl_file_parse['FILE_NAME_BAND_' + str(N)])
            for N in [1, 2, 3, 4, 5, 6, 7, 9]]
        # get the thermal file names bands
        thermal_bands = [
            os.path.join(input_dir, mtl_file_parse['FILE_NAME_BAND_' + str(N)])
            for N in [10, 11]]

    # set the prefer file name band for process
    reflective_bands = [get_prefer_name(file_path) for file_path in reflective_bands]
    thermal_bands = [get_prefer_name(file_path) for file_path in thermal_bands]

    ########################################
    # reflective bands stack

    # tmp file for reflective bands stack
    reflective_stack_file = os.path.join(tmp_dir, "reflective_stack.tif")

    if not os.path.isfile(reflective_stack_file):
        gdal_merge.main(["", "-separate", "-of", "GTiff", "-o",
                         reflective_stack_file] + reflective_bands)

    ########################################
    # thermal bands stack

    # tmp file for reflective bands stack
    thermal_stack_file = os.path.join(tmp_dir, "thermal_stack.tif")

    if not os.path.isfile(thermal_stack_file):
        gdal_merge.main(["", "-separate", "-of", "GTiff", "-o",
                         thermal_stack_file] + thermal_bands)

    ########################################
    # estimates of per-pixel angles for sun
    # and satellite azimuth and zenith
    #
    # fmask_usgsLandsatMakeAnglesImage.py

    # tmp file for angles
    angles_file = os.path.join(tmp_dir, "angles.tif")

    mtlInfo = config.readMTLFile(mtl_file)

    imgInfo = fileinfo.ImageInfo(reflective_stack_file)
    corners = landsatangles.findImgCorners(reflective_stack_file, imgInfo)
    nadirLine = landsatangles.findNadirLine(corners)

    extentSunAngles = landsatangles.sunAnglesForExtent(imgInfo, mtlInfo)
    satAzimuth = landsatangles.satAzLeftRight(nadirLine)

    landsatangles.makeAnglesImage(reflective_stack_file, angles_file,
                                  nadirLine, extentSunAngles, satAzimuth, imgInfo)

    ########################################
    # saturation mask
    #
    # fmask_usgsLandsatSaturationMask.py

    # tmp file for angles
    saturationmask_file = os.path.join(tmp_dir, "saturationmask.tif")

    if landsat_version == 4:
        sensor = config.FMASK_LANDSAT47
    elif landsat_version == 5:
        sensor = config.FMASK_LANDSAT47
    elif landsat_version == 7:
        sensor = config.FMASK_LANDSAT47
    elif landsat_version == 8:
        sensor = config.FMASK_LANDSAT8

    # needed so the saturation function knows which
    # bands are visible etc.
    fmaskConfig = config.FmaskConfig(sensor)

    saturationcheck.makeSaturationMask(fmaskConfig, reflective_stack_file,
                                       saturationmask_file)

    ########################################
    # top of Atmosphere reflectance
    #
    # fmask_usgsLandsatTOA.py

    # tmp file for toa
    toa_file = os.path.join(tmp_dir, "toa.tif")

    landsatTOA.makeTOAReflectance(reflective_stack_file, mtl_file, angles_file, toa_file)

    ########################################
    # cloud mask
    #
    # fmask_usgsLandsatStacked.py

    # tmp file for cloud
    cloud_fmask_file = os.path.join(tmp_dir, "fmask.tif")

    # 1040nm thermal band should always be the first (or only) band in a
    # stack of Landsat thermal bands
    thermalInfo = config.readThermalInfoFromLandsatMTL(mtl_file)

    anglesInfo = config.AnglesFileInfo(angles_file, 3, angles_file,
                                       2, angles_file, 1, angles_file, 0)

    if landsat_version == 4:
        sensor = config.FMASK_LANDSAT47
    elif landsat_version == 5:
        sensor = config.FMASK_LANDSAT47
    elif landsat_version == 7:
        sensor = config.FMASK_LANDSAT47
    elif landsat_version == 8:
        sensor = config.FMASK_LANDSAT8

    fmaskFilenames = config.FmaskFilenames()
    fmaskFilenames.setTOAReflectanceFile(toa_file)
    fmaskFilenames.setThermalFile(thermal_stack_file)
    fmaskFilenames.setOutputCloudMaskFile(cloud_fmask_file)
    fmaskFilenames.setSaturationMask(saturationmask_file)  # TODO: optional

    fmaskConfig = config.FmaskConfig(sensor)
    fmaskConfig.setThermalInfo(thermalInfo)
    fmaskConfig.setAnglesInfo(anglesInfo)
    fmaskConfig.setKeepIntermediates(False)
    fmaskConfig.setVerbose(False)
    fmaskConfig.setTempDir(tmp_dir)

    # Set the settings fmask filters from widget to FmaskConfig
    fmaskConfig.setMinCloudSize(min_cloud_size)
    fmaskConfig.setEqn17CloudProbThresh(cloud_prob_thresh)
    fmaskConfig.setCloudBufferSize(int(cloud_buffer_size))
    fmaskConfig.setShadowBufferSize(int(shadow_buffer_size))
    fmaskConfig.setCirrusProbRatio(cirrus_prob_ratio)
    fmaskConfig.setEqn19NIRFillThresh(nir_fill_thresh)
    fmaskConfig.setEqn1Swir2Thresh(swir2_thresh)
    fmaskConfig.setEqn2WhitenessThresh(whiteness_thresh)
    fmaskConfig.setEqn7Swir2Thresh(swir2_water_test)
    fmaskConfig.setEqn20NirSnowThresh(nir_snow_thresh)
    fmaskConfig.setEqn20GreenSnowThresh(green_snow_thresh)

    # set to 1 for all Fmask filters disabled
    if filters_enabled["Fmask Cloud"]:
        fmask.OUTCODE_CLOUD = 2
    else:
        fmask.OUTCODE_CLOUD = 1

    if filters_enabled["Fmask Shadow"]:
        fmask.OUTCODE_SHADOW = 3
    else:
        fmask.OUTCODE_SHADOW = 1

    if filters_enabled["Fmask Snow"]:
        fmask.OUTCODE_SNOW = 4
    else:
        fmask.OUTCODE_SNOW = 1

    if filters_enabled["Fmask Water"]:
        fmask.OUTCODE_WATER = 5
    else:
        fmask.OUTCODE_WATER = 1

    # process Fmask
    fmask.doFmask(fmaskFilenames, fmaskConfig)

    return cloud_fmask_file
    

def do_blue_band(mtl_file, blue_band_l457, blue_band_l8, tmp_dir):

    input_dir = os.path.dirname(mtl_file)

    # parser
    mtl_file_parse = mtl2dict(mtl_file)

    # get the landsat version
    landsat_version = int(mtl_file_parse['SPACECRAFT_ID'][-1])

    # tmp file for cloud
    cloud_bb_file = os.path.join(tmp_dir, "bb_mask.tif")

    #if args.blue_band_l457 != 1 and args.blue_band_l8 != 1

    ########################################
    # select the Blue Band
    if landsat_version in [4, 5, 7]:
        # get the reflective file names bands
        blue_band_file = os.path.join(input_dir, mtl_file_parse['FILE_NAME_BAND_1'])
        bb_threshold = blue_band_l457
    if landsat_version in [8]:
        # get the reflective file names bands
        blue_band_file = os.path.join(input_dir, mtl_file_parse['FILE_NAME_BAND_2'])
        bb_threshold = blue_band_l8

    if bb_threshold == -1:
        return

    print("Blue band: ", end="")

    # fix file name
    blue_band_file = get_prefer_name(blue_band_file)

    ########################################
    # do blue band filter
    gdal_calc.Calc(calc="1*(A<{threshold})+6*(A>={threshold})".format(threshold=bb_threshold),
                   A=blue_band_file, outfile=cloud_bb_file, type="Byte")

    # save final result of masking
    return cloud_bb_file

    print("done")


def mtl2dict(filename, to_float=True):
    """ Reads in filename and returns a dict with MTL metadata.
    """

    assert os.path.isfile(filename), '{} is not a file'.format(filename)

    mtl = {}

    # Open filename with context manager
    with open(filename, 'r') as f:
        # Read all lines in file
        for line in f.readlines():
            # Split KEY = VALUE entries
            key_value = line.strip().split(' = ')

            # Ignore END lines
            if len(key_value) != 2:
                continue

            key = key_value[0].strip()
            value = key_value[1].strip('"')

            # Try to convert to float
            if to_float is True:
                try:
                    value = float(value)
                except:
                    pass
            # add to dict
            mtl[key] = value

    return mtl


def get_prefer_name(file_path):
    """Search the prefer name for band: band1 > B1"""
    path_dir, band_file = os.path.split(file_path)
    # prefer thermal b61/2 over band61/2 over B6_VCID_1/2 in Landsat 7
    if band_file.startswith("LE7") or band_file.startswith("LE07"):
        file_bandN = band_file.replace("_B6_VCID_", "_b6").replace(".TIF", ".tif")
        if os.path.isfile(os.path.join(path_dir, file_bandN)):
            return os.path.join(path_dir, file_bandN)
        file_bandN = band_file.replace("_B6_VCID_", "_band6").replace(".TIF", ".tif")
        if os.path.isfile(os.path.join(path_dir, file_bandN)):
            return os.path.join(path_dir, file_bandN)
    # prefer bN over bandN over BN (i.e. band1.tif over B1.TIF)
    file_bandN = band_file.replace("_B", "_b").replace(".TIF", ".tif")
    if os.path.isfile(os.path.join(path_dir, file_bandN)):
        return os.path.join(path_dir, file_bandN)
    file_bandN = band_file.replace("_B", "_band").replace(".TIF", ".tif")
    if os.path.isfile(os.path.join(path_dir, file_bandN)):
        return os.path.join(path_dir, file_bandN)
    # return original
    return file_path


if __name__ == '__main__':
    script()
