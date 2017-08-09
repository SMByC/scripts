#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2017 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
# Compute the pyramids for input tif
#

# break with any error
set -e

##### help
function help(){ cat << END
usage: pyramids [-h] FILES

Compute the pyramids inside the tif image (with compression)

arguments:
    FILES  files to process

For more information visit:
https://smbyc.bitbucket.io/scripts/pyramids
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
#####

function clean () {
    gdal_translate $1 tmp.tif
    rm $1
    mv tmp.tif $1
}

function compression () {
    # better use DEFLATE compression but not compatibility wit Erdas
    gdal_translate -co BIGTIFF=YES -co COMPRESS=LZW -co PREDICTOR=2 $1 tmp.tif
    rm $1
    mv tmp.tif $1
}

function pyramids () {
    gdaladdo -r average --config BIGTIFF_OVERVIEW YES $1 2 4 6 8 12 16 24 32
}

echo -e "\nCompute the pyramids:\n"

for FILE in "$@"
do
    echo "step 1: compression: $FILE"
    compression $FILE
    echo "step 2: compute the pyramids: $FILE"
    pyramids $FILE
done

echo "DONE"