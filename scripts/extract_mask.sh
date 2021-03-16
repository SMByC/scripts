#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2018 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
# Extract mask
#

# break with any error
#set -e

##### help
function help(){ cat << END
usage: extract-mask [-h][--inverted] FILES

Extract the mask where 0=data 1=mask

arguments:
    --inverted  create the mask with inverted values, 0=mask 1=data
    FILES  files to process

For more information visit:
https://smbyc.bitbucket.io/scripts
END
}

if (( $# < 1 )); then
    echo -e "Error: required arguments, see how to usage:\n"
    help
    exit 1
fi

REVERSE=false

for arg in "$@"
do
    if [[ $arg == "-h" ]]
    then
        help
        exit 0
    fi
    if [[ $arg == "--inverted" ]]
    then
        REVERSE=true
    fi
done
#####

for FILE in "$@"
do
    if [[ $FILE == -* ]]; then
        continue
    fi

    echo "Extracting mask: $FILE"
    out_name=$(echo "$FILE" | cut -d'.' -f1)
    extension=$(echo "$FILE" | rev | cut -d'.' -f1 | rev)

    if [ $extension == "tif" ]; then
        # unset nodata
        gdal_edit.py "$FILE" -unsetnodata
        if [ "$REVERSE" = true ] ; then
            gdal_calc.py -A "$FILE" --type=Byte --co COMPRESS=PACKBITS --calc="1*(A!=0)+0*(A==0)" --outfile="${out_name}"_mask.tif --NoDataValue=1 --quiet
        else
            gdal_calc.py -A "$FILE" --type=Byte --co COMPRESS=PACKBITS --calc="0*(A!=0)+1*(A==0)" --outfile="${out_name}"_mask.tif --NoDataValue=0 --quiet
        fi
        echo "   mask file: ${out_name}_mask.tif"
    else
        echo "   this file is not a .tif"
    fi
done

echo -e "\nDONE"