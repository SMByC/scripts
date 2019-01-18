#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2019 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
# Convert raw Landsat product (level 1) to ESPA (level 2)
#

# break with any error
#set -e

##### help
function help(){ cat << END
usage: lpgs-to-espa [-h] DIRS

Convert raw Landsat product (LPGS - level 1) to ESPA (level 2)

arguments:
    DIRS  directories to process

For more information visit:
https://smbyc.bitbucket.io/scripts/extract_landsat_files
END
}

if (( $# < 1 )); then
    echo -e "Error: required arguments, see how to usage:\n"
    help
    exit 1
fi

for arg in "$@"
do
    if [[ $arg == "-h" ]]
    then
        help
        exit 0
    fi
done

##### DEFINITIONS
export PREFIX="/home/smbyc/xtremio/imagenes/Prueba/ESPA"

export L8_AUX_DIR="/home/smbyc/xtremio/imagenes/Prueba/ESPA/static_data"
export LEDAPS_AUX_DIR="/home/smbyc/xtremio/imagenes/Prueba/ESPA/static_data"
export ESPA_LAND_MASS_POLYGON="/home/smbyc/xtremio/imagenes/Prueba/ESPA/static_data/land_no_buf.ply"

export TIFFINC="/usr/include"
export TIFFLIB="/usr/lib64"
export GEOTIFF_INC="/usr/include/libgeotiff"
export GEOTIFF_LIB="/usr/lib64"
export HDFINC="/usr/include/hdf"
export HDFLIB="/usr/lib64/hdf"
export HDFEOS_GCTPINC="/home/smbyc/xtremio/imagenes/Prueba/ESPA/extra_libs/include"
export HDFEOS_GCTPLIB="/home/smbyc/xtremio/imagenes/Prueba/ESPA/extra_libs/lib"
export HDFEOS_INC="/home/smbyc/xtremio/imagenes/Prueba/ESPA/extra_libs/hdfeos/include"
export HDFEOS_LIB="/home/smbyc/xtremio/imagenes/Prueba/ESPA/extra_libs/lib"
export HDFEOS5_INC="/home/smbyc/xtremio/imagenes/Prueba/ESPA/extra_libs/hdfeos5/include"
export HDFEOS5_LIB="/home/smbyc/xtremio/imagenes/Prueba/ESPA/extra_libs/lib"
export JPEGINC="/usr/include"
export JPEGLIB="/usr/lib64"
export XML2INC="/usr/include/libxml2"
export XML2LIB="/usr/include/libxml2"
export JBIGINC="/usr/include"
export JBIGLIB="/usr/lib64"
export ZLIBINC="/usr/include"
export ZLIBLIB="/usr/lib64"
export ESPAINC="/home/smbyc/xtremio/imagenes/Prueba/ESPA/espa-product-formatter/raw_binary/include"
export ESPALIB="/home/smbyc/xtremio/imagenes/Prueba/ESPA/espa-product-formatter/raw_binary/lib"
export ESPA_LEVEL2QA_INC="/home/smbyc/xtremio/imagenes/Prueba/ESPA/espa-l2qa-tools/include"
export ESPA_LEVEL2QA_LIB="/home/smbyc/xtremio/imagenes/Prueba/ESPA/espa-l2qa-tools/lib"

export NCDF4INC="/usr/include"
export NCDF4LIB="/usr/lib64"
export HDF5INC="/usr/include"
export HDF5LIB="/usr/lib64"
export CURLINC="/usr/include"
export CURLLIB="/usr/lib64"
export IDNINC="/usr/include"
export IDNLIB="/usr/lib64"
export ZLIBLIB="/usr/lib64"

export ESPA_SCHEMA="/home/smbyc/xtremio/imagenes/Prueba/ESPA/espa-product-formatter/schema/espa_internal_metadata_v2_0.xsd"

export PATH="/home/smbyc/xtremio/imagenes/Prueba/ESPA/bin:$PATH"

##### RUN

echo -e "\nConvert raw Landsat product (LPGS - level 1) to ESPA (level 2)"

for DIR in "$@"
do
    echo -e "\nCONVERTING: $DIR \n"
    cd $DIR
    for MTL in `ls *_MTL.txt`; do
        echo $MTL

        BASE_NAME=$(basename -- "$MTL")
        BASE_NAME="${BASE_NAME%_MTL.txt*}"
        echo $BASE_NAME

        convert_lpgs_to_espa --mtl $MTL

        if [[ $BASE_NAME == "LC08"* || $BASE_NAME == "LC8"* ]]; then
            do_lasrc.py --xml ${BASE_NAME}.xml
        fi
        if [[ $BASE_NAME == "LE07"* || $BASE_NAME == "LE7"* ]]; then
            do_ledaps.py --xml ${BASE_NAME}.xml
        fi

        generate_pixel_qa --xml ${BASE_NAME}.xml
        convert_espa_to_gtif --xml ${BASE_NAME}.xml --gtif $BASE_NAME

        rm *.hdr *.img *.tfw
    done
done

echo -e "\nDONE"