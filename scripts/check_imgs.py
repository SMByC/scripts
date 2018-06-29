import datetime
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

        # check SMByC finename
        try:
            filename = os.path.basename(img_file).split(".")[0]
            path = int(filename.split("_")[1])
            row = int(filename.split("_")[2])
            date = datetime.datetime.strptime(filename.split("_")[3], "%y%m%d").date()
            jday = date.timetuple().tm_yday
            landsat_version = int(filename.split("_")[4][0])
            sensor = filename.split("_")[4][1::]
            if not filename.startswith("Landsat_"): raise Exception("No inicia con'Landsat_'")
            if sensor not in ["ETM", "OLI", "TM"]: raise Exception("Nombre de sensor '{}' invalido".format(sensor))
            if landsat_version not in [5, 7, 8]: raise Exception("Version de landsat '{}' invalido".format(landsat_version))
            if os.path.basename(os.path.dirname(img_file)) != "{}_{}".format(path, row):
                raise Exception("Path/row de la imagen '{}' no corresponde a la carpeta superior '{}'"
                                .format("{}_{}".format(path, row), os.path.basename(os.path.dirname(img_file))))

            parent_dir = os.path.basename(os.path.dirname(os.path.dirname(img_file)))
            if parent_dir == "3.2.1.Reflectancia_SR":
                ptype = filename.split("_")[5:7]
                if ptype != ["Reflec", "SR"]: raise Exception("Archivo dentro de la carpeta '{}' debe finalizar con 'Reflec_SR'".format(parent_dir))
            if parent_dir == "3.2.2.Reflectancia_SR_Enmascarada":
                ptype = filename.split("_")[5:8]
                if ptype != ["Reflec", "SR", "Enmask"]: raise Exception("Archivo dentro de la carpeta '{}' debe finalizar con 'Reflec_SR_Enmask'".format(parent_dir))
            if parent_dir == "3.2.3.Reflectancia_Normalizada":
                ptype = filename.split("_")[5:6]
                if ptype != ["Norm"]: raise Exception("Archivo dentro de la carpeta '{}' debe finalizar con 'Norm'".format(parent_dir))

        except Exception as e:
            errors += "\t- Error en el nombre de la imagen: {}\n".format(e)

        if errors != "":
            print("\nERRORES PARA: " + img_file + ":")
            print(errors)
            imgs_with_problems += 1

    print("\nDONE: Images with problems: {} of {}\n".format(imgs_with_problems, len(img_files)))


if __name__ == '__main__':
    script()
