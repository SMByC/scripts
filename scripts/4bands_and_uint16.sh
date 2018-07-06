#!/usr/bin/env bash

##### help
function help(){ cat << END
usage: 4bands-and-uint16 [-h] FILES

Re-stack to 4 bands and convert to UInt16

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

function process () {
    echo "Process: $1"

    out_name=`echo $1 | cut -d'.' -f1`

    for band in $(seq 1 4); do
        gdal_translate -a_nodata none -ot UInt16 -b ${band} $1 ${band}.tif
    done

    gdal_merge.py -ot "UInt16" -co BIGTIFF=YES -o ${out_name}_4bands.tif \
        -separate 1.tif 2.tif 3.tif 4.tif

    rm 1.tif 2.tif 3.tif 4.tif

}

echo -e "\nRe-stack to 4 bands and convert to UInt16:\n"

for FILE in "$@"
do
    extension=`echo $FILE | cut -d'.' -f2-3`
    if [ $extension == "tif" ]; then
        process $FILE
    fi
done

echo -e "\nDONE"
