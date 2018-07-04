import os, sys
import argparse
from osgeo import gdal
gdal.UseExceptions()
gdal.PushErrorHandler('CPLQuietErrorHandler')

# add project dir to pythonpath
libs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "libs")
if libs_dir not in sys.path:
    sys.path.append(libs_dir)

import gdal_merge, gdal_calc


def script():
    """Run as a script with arguments
    """
    parser = argparse.ArgumentParser(
        prog='enmask',
        description='Apply the mask for all images in input directory (scene) or files')

    parser.add_argument('inputs', type=str, help='directories or files to enmask', nargs='*', default=".")
    args = parser.parse_args()

    # search all Image files in inputs recursively if the files are in directories
    img_files = []
    for _input in args.inputs:
        if os.path.isfile(_input):
            if _input.endswith(('.tif', '.TIF')):
                img_files.append(_input)
        elif os.path.isdir(_input):
            for root, dirs, files in os.walk(_input):
                if len(files) != 0:
                    files = [os.path.join(root, x) for x in files if x.endswith(('.tif', '.TIF'))]
                    [img_files.append(file) for file in files]

    # process
    print("\nWORKING DIRECTORY: {}".format(os.path.dirname(os.path.abspath(img_files[0]))))
    print("\nIMAGES TO PROCESS: {}\n".format(len(img_files)))
    imgs_with_problems = 0
    for img_file in img_files:
        filename = os.path.basename(img_file).split(".")[0]
        path_row = os.path.basename(os.path.dirname(os.path.abspath(img_file)))
        print("Processing '{}': ".format(img_file), end="")
        mask_file = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(img_file))))))
        mask_file = os.path.join(mask_file, "6.Procesos_Mosaico_Anual", "6.2.Enmascaramiento_Nubes",
                                 path_row, filename.replace("_Reflec", "_Mask.tif"))

        if not os.path.isfile(mask_file):
            print("ERROR, mask file not exist:\n\t{}".format(mask_file))
            imgs_with_problems += 1
            continue

        enmask_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(img_file))))), "3.2.Reflectancia_SR", "3.2.2.Reflectancia_SR_Enmascarada",
                                   path_row, filename.replace("_Reflec", "_SR_Enmask.tif"))

        if os.path.isfile(enmask_file):
            enmask_file = enmask_file.replace("_SR_Enmask.tif", "_SR_Enmask_script.tif")
            if os.path.isfile(enmask_file):
                os.remove(enmask_file)

        gdal_calc.Calc(calc="A*(B==0)", A=os.path.abspath(img_file), B=mask_file,
                       outfile=enmask_file, allBands='A', overwrite=True)

        print("DONE")

    print("\nDONE: Images with problems: {} of {}\n".format(imgs_with_problems, len(img_files)))


if __name__ == '__main__':
    script()
