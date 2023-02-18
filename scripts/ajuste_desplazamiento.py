from osgeo import gdal # Open in read/write mode
import os
import argparse


def script():
    """Run as a script with arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('inputs', type=str, help='directories and/or files', nargs='*')
    parser.add_argument('-x', type=float, help='horizontal displacement (+) east (-) west, default: +10.992', default=10.992)
    parser.add_argument('-y', type=float, help='vertical displacement (+) north (-) south, default: +13.407', default=13.407)
    args = parser.parse_args()

    # search all Image files in inputs recursively if the files are in directories
    img_files = []
    for _input in args.inputs:
        if os.path.isfile(_input):
            if _input.endswith(('.tif', '.TIF')):
                img_files.append(os.path.abspath(_input))
        elif os.path.isdir(_input):
            for root, dirs, files in os.walk(_input):
                if len(files) != 0:
                    files = [os.path.join(root, x) for x in files if x.endswith(('.tif', '.TIF'))]
                    [img_files.append(os.path.abspath(file)) for file in files]

    # process
    print("\nIMAGES TO PROCESS: {}\n".format(len(img_files)))

    for target_file in img_files:
        print("PROCESSING: " + os.path.basename(target_file))
        # remove .aux.xml file
        if os.path.isfile(target_file + '.aux.xml'):
            os.remove(target_file + '.aux.xml')

        rast_src = gdal.Open(target_file, gdal.GA_ReadOnly)
        gt = rast_src.GetGeoTransform()

        # Convert tuple to list, so we can modify it
        gtl = list(gt)
        gtl[0] = gtl[0] + args.x  # Move horizontal
        gtl[3] = gtl[3] + args.y  # Move vertical
        # Save the geotransform to the raster
        rast_src.SetGeoTransform(tuple(gtl))
        out_filename = target_file.replace('.tif', '_A.tif')
        # save the raster to a new file
        gdal.GetDriverByName('GTiff').CreateCopy(out_filename, rast_src)
        rast_src = None
        del gt, gtl

        # remove .aux.xml file
        if os.path.isfile(target_file + '.aux.xml'):
            os.remove(target_file + '.aux.xml')

    print("DONE")


if __name__ == '__main__':
    script()