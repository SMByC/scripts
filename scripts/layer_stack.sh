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

##### help
function help(){ cat << END
usage: layer-stack [-h] FILES

Make the layerstack for all images in the input order

arguments:
    FILES  files to process in order to stack

For more information visit:
https://smbyc.bitbucket.io/scripts/layer_stack/
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

echo -e "\nMaking the layerstack for (and in the following order):\n$@\n"

if [[ $1 == *"_band"* ]]; then
    out_name=$(echo $1 | sed 's/_band.*$/_allbands.tif/g')
else
    out_name=$(echo $1 | sed 's/.tif/_allbands.tif/g')
fi

gdal_merge.py -o $out_name -of GTiff -co BIGTIFF=YES -separate $@

echo "Result saved in: $out_name"
echo "DONE"

