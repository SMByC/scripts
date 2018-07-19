#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2016-2017 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
from __future__ import print_function
from __future__ import unicode_literals

import os, sys
import argparse
import shutil

# add project dir to pythonpath
from subprocess import call

libs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "libs")
if libs_dir not in sys.path:
    sys.path.append(libs_dir)


def script():
    """Run as a script with arguments
    """
    parser = argparse.ArgumentParser(
        prog='sentinel-cloud-masking',
        description='Compute and generate the cloud mask (fmask) for all Sentinel input')

    parser.add_argument('inputs', type=str, help='directories or MTL files to process', nargs='*')

    args = parser.parse_args()

    print("\nLoading the metadata files: ", end="")
    # search all Image files in inputs recursively if the files are in directories
    metadata_files = []
    for _input in args.inputs:
        if os.path.isfile(_input):
            if _input == "metadata.xml":
                metadata_files.append(os.path.abspath(_input))
        elif os.path.isdir(_input):
            for root, dirs, files in os.walk(_input):
                if len(files) != 0:
                    files = [os.path.join(root, x) for x in files if x == "metadata.xml"]
                    [metadata_files.append(os.path.abspath(file)) for file in files]
    print("{} Sentinel to process\n".format(len(metadata_files)))

    for metadata_file in metadata_files:

        process_dir = os.path.dirname(metadata_file)
        print("PROCESSING: " + os.path.basename(process_dir))

        call("gdalbuildvrt -resolution user -tr 10 10 -separate allbands.vrt B0[1-8].jp2 B8A.jp2 B09.jp2 B1[0-2].jp2",
             shell=True, cwd=process_dir)

        call("export PYTHONPATH='{}' && ".format(libs_dir) + "python3.6 " + libs_dir+"/fmask/bin/fmask_sentinel2makeAnglesImage.py " + "-i metadata.xml -o angles.img",
             shell=True, cwd=process_dir)

        call("export PYTHONPATH='{}' && ".format(libs_dir) + "python3.6 " + libs_dir+"/fmask/bin/fmask_sentinel2Stacked.py " + "-a allbands.vrt -z angles.img -o cloud.img",
             shell=True, cwd=process_dir)

        os.remove(os.path.join(process_dir, "allbands.vrt"))
        os.remove(os.path.join(process_dir, "angles.img"))

        ### ending fmask process
        print("DONE\n")


if __name__ == '__main__':
    script()
