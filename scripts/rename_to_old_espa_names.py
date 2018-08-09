#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2016-2018 Xavier Corredor Llano, SMBYC
#  Email: xcorredorl at ideam.gov.co
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
from __future__ import print_function
from __future__ import unicode_literals

import os
import argparse
import shutil
import fileinput


def script():
    """Run as a script with arguments
    """
    parser = argparse.ArgumentParser(
        prog='rename-to-old-espa-names',
        description='Rename the new to old espa version names files')

    parser.add_argument('inputs', type=str, help='directories', nargs='*')

    args = parser.parse_args()

    print("\nDirectories to renames: ", end="")
    # search all Image files in inputs recursively if the files are in directories
    mtl_files = []
    dirs_target = []
    for _input in args.inputs:
        if os.path.isfile(_input):
            if _input.endswith("_MTL.txt") and _input[2] == "0":
                mtl_files.append(os.path.abspath(_input))
        elif os.path.isdir(_input):
            for root, dirs, files in os.walk(_input):
                if len(files) != 0:
                    files = [os.path.join(root, x) for x in files if x.endswith("_MTL.txt") and _input[2] == "0"]
                    [mtl_files.append(os.path.abspath(file)) for file in files]
                    [dirs_target.append(os.path.dirname(os.path.abspath(file))) for file in files]

    print(len(dirs_target))

    for mtl_file, dir_target in zip(mtl_files, dirs_target):
        print("\nRENAMING: " + os.path.basename(dir_target))

        input_dir = os.path.dirname(mtl_file)

        # parser
        mtl_file_parse = mtl2dict(mtl_file)

        from_filename = mtl_file_parse['LANDSAT_PRODUCT_ID']
        to_filename = mtl_file_parse['LANDSAT_SCENE_ID']

        files_to_delete = []

        for root, dirs, files in os.walk(dir_target):
            if len(files) != 0:
                for file in files:
                    if "_sr_band" in file:
                        new_filename = file.replace(from_filename, to_filename)
                        shutil.move(os.path.join(root, file), os.path.join(root, new_filename))
                        continue
                    if "_bt_band" in file:
                        new_filename = file.replace(from_filename, to_filename)
                        shutil.move(os.path.join(root, file), os.path.join(root, new_filename))
                        continue
                    if "_mask.tif" in file:
                        new_filename = file.replace(from_filename, to_filename)
                        shutil.move(os.path.join(root, file), os.path.join(root, new_filename))
                        continue
                    if "_MTL.txt" in file:
                        new_filename = file.replace(from_filename, to_filename)
                        shutil.move(os.path.join(root, file), os.path.join(root, new_filename))

                        # rename filename for bands and mtl inside mtl
                        with fileinput.FileInput(os.path.join(root, new_filename), inplace=True) as file:
                            for line in file:
                                if "FILE_NAME_BAND_" in line:
                                    band = line.split("FILE_NAME_BAND_")[1][0]
                                    try:
                                        old_filename = [f for f in files if "_sr_band"+band in f][0]
                                        line = "    FILE_NAME_BAND_{} = \"{}\"\n".format(band, old_filename.replace(from_filename, to_filename))
                                    except: pass
                                if "METADATA_FILE_NAME" in line:
                                    line = "    METADATA_FILE_NAME = \"{}\"\n".format(new_filename)
                                print(line, end='')
                        continue
                    files_to_delete.append(os.path.join(root, file))

        for f_delete in files_to_delete:
            os.remove(f_delete)

        shutil.move(input_dir, os.path.join(os.path.dirname(input_dir), to_filename))

        print("      TO: " + to_filename)


def mtl2dict(filename, to_float=True):
    """ Reads in filename and returns a dict with MTL metadata.
    """

    assert os.path.isfile(filename), '{} is not a file'.format(filename)

    mtl = {}

    # Open filename with context manager
    with open(filename, 'r') as f:
        # Read all lines in file
        for line in f.readlines():
            # Split KEY = VALUE entries
            key_value = line.strip().split(' = ')

            # Ignore END lines
            if len(key_value) != 2:
                continue

            key = key_value[0].strip()
            value = key_value[1].strip('"')

            # Try to convert to float
            if to_float is True:
                try:
                    value = float(value)
                except:
                    pass
            # add to dict
            mtl[key] = value

    return mtl


if __name__ == '__main__':
    script()
