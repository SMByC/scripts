#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2017 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
# Make the default layer stack for several landsat directories
#

echo -e "\nMake the default layer stack for all landsat folders in current directory.\n"

# default bands
BANDS="1,2,3,4,5,7"

# https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
for i in "$@"
do
case $i in
    -b=*)
    BANDS="${i#*=}"
    shift # past argument=value
    ;;
    *)
            # unknown option
    ;;
esac
done

echo -e "Bands to process: $BANDS\n"

for dir in `ls -d L*/`
do
    echo "Processing: $dir"
    cd $dir
    name=`ls *band*`
    out_name=`echo $name | cut -d's' -f1`

    gdal_merge.py -o ../${out_name}Reflec_SR.tif -of GTiff -co BIGTIFF=YES -ot UInt16 -separate $(eval ls ${out_name}sr_band{$BANDS}.tif)
    echo -e "  Result saved in: ${out_name}Reflec_SR.tif\n"

    cd ..
done

echo "DONE"
