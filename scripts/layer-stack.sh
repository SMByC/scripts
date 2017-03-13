#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2017 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
# Make the layer stack for the input images
#

# break with any error
set -e

echo -e "\nMaking the layerstack for (and in the following order):\n$@\n"

if [[ $1 == *"_band"* ]]; then
    out_name=$(echo $1 | sed 's/_band.*$/_allbands.tif/g')
else
    out_name=$(echo $1 | sed 's/.tif/_allbands.tif/g')
fi

gdal_merge.py -o $out_name -of GTiff -co BIGTIFF=YES -separate $@

echo "Result saved in: $out_name"
echo "DONE"

