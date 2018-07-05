import os, sys
from subprocess import call
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
    report = ""
    imgs_with_problems = 0
    for img_file in img_files:
        filename = os.path.basename(img_file).split(".")[0]
        if filename.endswith("_Reflec_C"):
            filename = filename.replace("_Reflec_C", "_Reflec")
        if filename.endswith("_Reflec_c"):
            filename = filename.replace("_Reflec_c", "_Reflec")
        path_row = os.path.basename(os.path.dirname(os.path.abspath(img_file)))
        report += "\nImage '{}': ".format(img_file)
        mask_file = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(img_file))))))
        mask_file = os.path.join(mask_file, "6.Procesos_Mosaico_Anual", "6.2.Enmascaramiento_Nubes",
                                 path_row, filename.replace("_Reflec", "_Mask.tif"))

        if not os.path.isfile(mask_file):
            report += "ERROR, mask file not exist:\n\t{}\n".format(mask_file)
            imgs_with_problems += 1
            #continue

        enmask_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(img_file))))), "3.2.Reflectancia_SR", "3.2.2.Reflectancia_SR_Enmascarada",
                                   path_row, filename.replace("_Reflec", "_SR_Enmask.tif"))

        if os.path.isfile(enmask_file):
            enmask_file = enmask_file.replace("_SR_Enmask.tif", "_SR_Enmask_script.tif")
            if os.path.isfile(enmask_file):
                os.remove(enmask_file)

        # unset the nodata
        tmp_file = enmask_file.replace(".tif", "_TMP.tif")
        img_file_open = gdal.Open(os.path.abspath(img_file))
        nbands = img_file_open.RasterCount
        del img_file_open

        if nbands == 6:
            bands_list = [3,4,5,6]
        elif nbands == 4:
            bands_list = [1,2,3,4]
        else:
            report += "ERROR, number of bands invalid: {}, expected 4 or 6\n".format(nbands)
            imgs_with_problems += 1
            continue

        tmp_bands = []
        for band in bands_list:
            tmp_band = enmask_file.replace(".tif", "_b{}.tif".format(band))
            call('gdal_translate -b {} -a_nodata none -ot UInt16 "{}" "{}"'.format(band, os.path.abspath(img_file), tmp_band), shell=True)
            tmp_bands.append(tmp_band)

        call("gdal_merge.py -co BIGTIFF=YES -o {} -separate {} {} {} {}".format(tmp_file, *tmp_bands), shell=True)

        try:
            gdal_calc.Calc(calc="A*(B==0)", A=tmp_file, B=mask_file,
                           outfile=enmask_file, allBands='A', overwrite=True)
            report += "DONE\n"
        except Exception as e:
            report += "ERROR applying the mask: {}\n".format(e)
            imgs_with_problems += 1

        os.remove(tmp_file)
        for tmp in tmp_bands:
            os.remove(tmp)

    print(report)
    print("\nDONE: Images with problems: {} of {}\n".format(imgs_with_problems, len(img_files)))


if __name__ == '__main__':
    script()
