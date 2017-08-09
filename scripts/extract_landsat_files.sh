#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2017 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
# Extract all input landsat compressed (tar.gz) files
#

# break with any error
# set -e

##### help
function help(){ cat << END
usage: extract-landsat-files [-h] FILES

Extract all input landsat compressed (tar.gz) files

arguments:
    FILES  files to process

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
#####

function extraction () {
    if [ -d "$2" ]; then
        echo "   the dir: $2 already exists, no extract!"
    else
        mkdir $2
        tar -zxf $1 -C $2 > /dev/null 2>&1
    fi
}

echo -e "\nExtract the landsat files:\n"

for FILE in "$@"
do
    echo "Extracting: $FILE"
    out_name=`echo $FILE | cut -d'.' -f1`
    extension=`echo $FILE | cut -d'.' -f2-3`
    if [ $extension == "tar.gz" ]; then
        extraction $FILE $out_name
    else
        echo "   this file is not a .tar.gz"
    fi
done

echo -e "\nDONE"