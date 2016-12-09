#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMBYC - IDEAM 2016
#  Authors: Xavier Corredor Llano
#  Email: xcorredorl at ideam.gov.co
#
# Busca recursivamente los archivos especificos (segun el tipo/extension)
# para el renombre de archivos lantsat por lotes y por lo tanto masivamente
# con base en la estructura definida dentro del proyecto SMBYC.
#

import os
import argparse
import datetime
from shutil import move

# tipo de renombre: "reflec", "mask", "enmask", "mtl", "norm", "aefectiva", "compuesto"
# dejar None para correrlo con argumentos
type_rename = "mtl"

# ruta para renombrar (busca recursivamente dentro de esta ruta)
dir_files = r"H:\ejemplo\de\ruta\en\windows"

if type_rename is None or type_rename == "" and dir_files is None or dir_files == "":
    # Create parser arguments
    arguments = argparse.ArgumentParser(
        prog="rename_landsat",
        description="Rename landsat",
        epilog="Xavier Corredor Llano <xcorredorl@ideam.gov.co>\n"
               "Sistema de Monitoreo de Bosques y Carbono - SMBYC\n"
               "IDEAM, Colombia",
        formatter_class=argparse.RawTextHelpFormatter)

    arguments.add_argument('-t', type=str, help='type for rename', required=True,
                           choices=("reflec", "mask", "enmask", "mtl", "norm", "aefectiva", "compuesto"))

    arguments.add_argument('dir_files', type=str, help='dir to get files for rename')

    arg = arguments.parse_args()

    type_rename = arg.t
    dir_files = arg.dir_files

if not os.path.isdir(dir_files):
    print "No existe el directorio"

pattern_search = ('.tif', '.TIF', '.aux', '.AUX', '.rrd', '.RDD', 'img', 'IMG')

if type_rename == "reflec":
    suffix = "_Reflec_SR"

if type_rename == "mask":
    suffix = "_Mask"

if type_rename == "enmask":
    suffix = "_Reflec_SR_Enmask"

if type_rename == "mtl":
    pattern_search = "_MTL.txt"
    suffix = '_Reflec_SR_MTL'

if type_rename == "norm":
    suffix = "_Norm"

if type_rename == "aefectiva":
    pattern_search = '.shp'
    suffix = "_Area_Efectiva.shp"

if type_rename == "compuesto":
    suffix = "_Compuesto"


def parse_landsat_ID(landsat_id):
    landsat_id = landsat_id.upper()
    if landsat_id[1] == "E":
        sensor = "ETM"
    if landsat_id[1] in ["O", "C"]:
        sensor = "OLI"
    if landsat_id[1] == "T":
        sensor = "TM"
    landsat_version = int(landsat_id[2])
    path = int(landsat_id[3:6])
    row = int(landsat_id[6:9])
    year = int(landsat_id[9:13])
    jday = int(landsat_id[13:16])
    date = CalcDate(year, jday)
    return sensor, landsat_version, path, row, date

def CalcDate(year, jday):
    return datetime.datetime(year, 1, 1) + datetime.timedelta(jday-1)

for root, dirs, files in os.walk(dir_files):
    if len(files) != 0:
        files = [x for x in files if x.endswith(pattern_search)]
        if files:
            for infile in files:

                landsat_id = infile.split("_")[0].split(".")[0]

                try:
                    sensor, landsat_version, path, row, date = parse_landsat_ID(landsat_id)
                    print "Renombrando la imagen: " + infile
                except:
                    continue

                ext = '.' + infile.split('.')[-1]

                outfile = "Landsat_{p}_{r}_{d}_{v}{s}".format(
                    p=path, r=row, d=date.strftime('%y%m%d'), v=landsat_version, s=sensor) + suffix + ext

                if type_rename == "aefectiva":
                    outfile = "Landsat_{p}_{r}".format(
                        p=path, r=row) + suffix + ext

                if type_rename == "compuesto":
                    outfile = "Landsat_{p}_{r}_{y}".format(
                        p=path, r=row, y=date.year) + suffix + ext

                move(os.path.join(root, infile), os.path.join(root, outfile))

