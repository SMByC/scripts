#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2017 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
# Busca recursivamente los archivos especificos (segun el tipo/extension)
# para el renombre de archivos lantsat por lotes y por lo tanto masivamente
# con base en la estructura definida dentro del proyecto SMBYC.
#
from __future__ import print_function
from __future__ import unicode_literals

import os
import argparse
import datetime
from shutil import move

# tipo de renombre: "reflec", "mask", "enmask", "mtl", "norm", "aefectiva", "compuesto"
# dejar None para correrlo con argumentos
type_rename = ""

# ruta para renombrar (busca recursivamente dentro de esta ruta)
dir_files = r""

if type_rename in ["", None] or dir_files in ["", None]:
    # Create parser arguments
    arguments = argparse.ArgumentParser(
        prog="rename_landsat",
        description="Rename landsat to SMByC format structure",
        epilog="Xavier Corredor Llano <xcorredorl@ideam.gov.co>\n"
               "Sistema de Monitoreo de Bosques y Carbono - SMBYC\n"
               "IDEAM, Colombia",
        formatter_class=argparse.RawTextHelpFormatter)

    arguments.add_argument('-t', type=str, help='type for rename', required=True,
                           choices=("reflec", "mask", "enmask", "mtl", "norm", "aefectiva", "compuesto"))
    arguments.add_argument('dir_files', type=str, help='directories and/or files', nargs='+')
    arg = arguments.parse_args()

    type_rename = arg.t
    dir_files = arg.dir_files

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


def parse_landsat_ID_oldFilename(landsat_id):
    # LC80070592016320LGN00_band1.tif
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


def parse_landsat_ID_newFilename(landsat_id):
    # LC08_L1TP_007059_20161115_20170318_01_T2_b1.tif
    # ['LC08', 'L1TP', '007059', '20161115']

    landsat_id = [i.upper() for i in landsat_id]
    if landsat_id[0][1] == "E":
        sensor = "ETM"
    if landsat_id[0][1] in ["O", "C"]:
        sensor = "OLI"
    if landsat_id[0][1] == "T":
        sensor = "TM"
    landsat_version = int(landsat_id[0][-1])
    path = int(landsat_id[2][0:3])
    row = int(landsat_id[2][3:6])
    year = int(landsat_id[3][0:4])
    month = int(landsat_id[3][4:6])
    day = int(landsat_id[3][6:8])
    date = datetime.date(year, month, day)
    return sensor, landsat_version, path, row, date


def CalcDate(year, jday):
    return datetime.datetime(year, 1, 1) + datetime.timedelta(jday-1)

all_files = []
all_dirs = []
for entry in dir_files:
    if os.path.isfile(entry):
        if entry.endswith(pattern_search):
            all_files.append(entry)
    elif os.path.isdir(entry):
        all_dirs.append(entry)

print(all_dirs)
for dir in all_dirs:
    for root, dirs, files in os.walk(dir):
        if len(files) != 0:
            files = [x for x in files if x.endswith(pattern_search)]
            if files:
                for infile in files:
                    all_files.append(os.path.join(root, infile))

files_renamed = []
finished_with_errors = 0
for path_file in all_files:
    root, infile = os.path.split(path_file)

    try:
        if infile[4] == "_":  # new ESPA filename
            landsat_id = infile.split("_")[0:4]
            sensor, landsat_version, path, row, date = parse_landsat_ID_newFilename(landsat_id)
        else:  # old filename
            landsat_id = infile.split("_")[0].split(".")[0]
            sensor, landsat_version, path, row, date = parse_landsat_ID_oldFilename(landsat_id)
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

    if os.path.join(root, outfile) not in files_renamed and not os.path.isfile(os.path.join(root, outfile)):
        print("Renombrando la imagen:")
        print("  ruta: " + root)
        print("    de: " + infile)
        print("     a: " + outfile +"\n")
    else:
        print("ERROR renombrando la imagen:")
        print("  ruta: " + root)
        print("    de: " + infile)
        print("     a: " + outfile)
        if os.path.join(root, outfile) in files_renamed:
            print(" ¡El nombre de archivo de destino ya ha sido renombrado\n"
                  "  con el mismo nombre y ruta, existen varios archivos que\n"
                  "  generan el mismo nombre de archivo de salida!\n")
        else:
            print(" ¡El nombre de archivo de destino ya existe en el sistema\n"
                  "  no se renombra para no sobreescribir el archivo existente!\n")
        finished_with_errors += 1
        continue

    move(os.path.join(root, infile), os.path.join(root, outfile))

    files_renamed.append(os.path.join(root, outfile))

print("Total de archivos renombrados: {}\n".format(len(files_renamed)))

if finished_with_errors > 0:
    print("Atención, finalizó con {} errores, por favor revise\n"
          "los mensajes anteriores del proceso por archivo.\n".format(finished_with_errors))

