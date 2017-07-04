#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2017 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
# extract all input landsat compressed (tar.gz) files
#

# break with any error
set -e

function extraction () {
    if [ -d "$2" ]; then
        echo "   the dir: $2 already exists, no extract!"
    else
        mkdir $2
        tar -zxf $1 -C $2
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