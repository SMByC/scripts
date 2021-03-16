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
usage: extract-mask [-h] FILES

Extract the mask

arguments:
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

for arg in "$@"
do
    if [[ $arg == "-h" ]]
    then
        help
        exit 0
    fi
done
#####

for FILE in "$@"
do
    echo "Extracting the mask: $FILE"
    out_name=$(echo "$FILE" | cut -d'.' -f1)
    extension=$(echo "$FILE" | rev | cut -d'.' -f1 | rev)
    # unset nodata
    gdal_edit.py "$FILE" -unsetnodata

    if [ $extension == "tif" ]; then
        gdal_calc.py -A "$FILE" --type=Byte --co COMPRESS=PACKBITS --calc="0*(A!=0)+1*(A==0)" --outfile="${out_name}"_mask.tif --NoDataValue=0
    else
        echo "   this file is not a .tif"
    fi
done

echo -e "\nDONE"