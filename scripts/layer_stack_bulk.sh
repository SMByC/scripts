#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2018 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
# Make the default layer stack for several landsat directories
#

# break with any error
set +e

##### help
function help(){ cat << END
usage: layer-stack-bulk [-h] [-b=BANDS] DIRS

Make the default (Reflec SR) layer stack for all landsat folders (L*) in current directory

arguments:
    BANDS  bands to make layer stack, by default 1-7 (e.g. -b=3,4,5)

For more information visit:
https://smbyc.bitbucket.io/scripts/layer_stack/#bulk-for-landsat
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

for DIR in "$@"
do
    if [ ! -d "$DIR" ]; then
        continue
    fi

    echo "Processing: $DIR"
    cd "$DIR"
    name=$(ls *sr_band* 2> /dev/null)
    if [ -n "$name" ]
    then
      # landsat 5, 7, 8
      out_name=$(echo $name | cut -d's' -f1)
      extension=$(echo $name | tail -c 4)
      gdal_merge.py -o ../${out_name}Reflec_SR.tif -of GTiff -co BIGTIFF=YES -ot Int16 -separate $(eval ls ${out_name}sr_band{$BANDS}.${extension})
      echo -e "  Result saved in: ${out_name}Reflec_SR.tif\n"
    else
      # landsat 9
      name=$(ls *SR_B*)
      if [ -n "$name" ]
      then
        out_name=$(echo $name | cut -d'R' -f1| head -c -2)
        extension=$(echo $name | tail -c 4)
        gdal_merge.py -o ../${out_name}Reflec_SR.tif -of GTiff -co BIGTIFF=YES -ot Int16 -separate $(eval ls ${out_name}SR_B{$BANDS}.${extension})
        echo -e "  Result saved in: ${out_name}Reflec_SR.tif\n"
      else
        name=$(ls *_B*)
        out_name=$(echo $name | cut -d'B' -f1| head -c -1)
        extension=$(echo $name | tail -c 4)
        gdal_merge.py -o ../${out_name}Reflec_SR.tif -of GTiff -co BIGTIFF=YES -ot Int16 -separate $(eval ls ${out_name}B{$BANDS}.${extension})
        echo -e "  Result saved in: ${out_name}Crudas.tif\n"
      fi
    fi

    cd ..
done

echo "DONE"
