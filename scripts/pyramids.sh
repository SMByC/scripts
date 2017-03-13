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

function clean () {
    gdal_translate $1 tmp.tif
    rm $1
    mv tmp.tif $1
}

function compression () {
    gdal_translate -co BIGTIFF=YES -co COMPRESS=DEFLATE -co PREDICTOR=2 $1 tmp.tif
    rm $1
    mv tmp.tif $1
}

function pyramids () {
    gdaladdo --config BIGTIFF_OVERVIEW YES $1 2 4 8 16 32 64 128 256 512
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