import os
import argparse
from osgeo import gdal
from osgeo import osr
gdal.UseExceptions()
gdal.PushErrorHandler('CPLQuietErrorHandler')


def script():
    """Run as a script with arguments
    """
    parser = argparse.ArgumentParser(
        prog='check-imgs',
        description='Verified with several parameters for all images in input or current directory')

    parser.add_argument('inputs', type=str, help='directories or files to check', nargs='*', default=".")
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
    print("\nIMAGES TO PROCESS: {}".format(len(img_files)))
    imgs_with_problems = 0
    for img_file in img_files:
        errors = ""
        try:
            gdal_file = gdal.Open(img_file, gdal.GA_ReadOnly)
        except:
            print("\nERRORES PARA: " + img_file + ":")
            errors += "\t- Archivo corrupto o invalido\n"
            print(errors)
            imgs_with_problems += 1
            continue

        if gdal_file.RasterCount != 4:
            errors += "\t- Imagen con {} bandas, esperado 4 bandas\n".format(gdal_file.RasterCount)

        # check the data type
        # 1: "int8",
        dtype = {1: "uint8", 2: "uint16", 3: "int16", 4: "uint32", 5: "int32",
                 6: "float32", 7: "float64", 10: "complex64", 11: "complex128"}

        if gdal_file.GetRasterBand(1).DataType not in [2, 4]:
            errors += "\t- Imagen con tipo de dato {}, esperado {}, {}\n".format(dtype[gdal_file.GetRasterBand(1).DataType], dtype[2], dtype[4])

        # projection
        proj = osr.SpatialReference(wkt=gdal_file.GetProjection())
        epsg = int(proj.GetAttrValue('AUTHORITY', 1))

        if epsg != 32618:
            errors += "\t- Imagen con sistema coordenadas {}, esperado {}\n".format(epsg, 32618)

        # pixel size
        pixel_size_x = abs(round(gdal_file.GetGeoTransform()[1], 3))
        pixel_size_y = abs(round(gdal_file.GetGeoTransform()[5], 3))
        if (pixel_size_x, pixel_size_y) != (30.0, 30.0):
            errors += "\t- Imagen con tamaño de pixel {}x{}, esperado 30.0x30.0\n".format(pixel_size_x, pixel_size_y)


        if errors != "":
            print("\nERRORES PARA: " + img_file + ":")
            print(errors)
            imgs_with_problems += 1

    print("\nDONE: Images with problems: {} of {}\n".format(imgs_with_problems, len(img_files)))


if __name__ == '__main__':
    script()
