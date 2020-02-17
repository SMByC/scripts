import datetime
import os
import argparse
import rasterio
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

    # statistics of number of files in path-row directory
    num_files_in_path_row = {}

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

        parent_dir = os.path.basename(os.path.dirname(os.path.dirname(img_file)))

        # exceptions
        if "6.4.Compuestos" in img_file:
            continue
        if "/Z19/" in img_file or "/z19/" in img_file or "/Z17/" in img_file or "/z17/" in img_file or \
           "/Z_19/" in img_file or "/z_19/" in img_file or "/Z_17/" in img_file or "/z_17/" in img_file or \
           "/19N/" in img_file or "/17N/" in img_file:
            continue

        # check the band number
        if img_file.endswith("Reflec_SR.tif"):
            if gdal_file.RasterCount != 6:
                errors += "\t- Imagen con {} bandas, esperado 6 bandas\n".format(gdal_file.RasterCount)
        elif parent_dir == "6.2.Enmascaramiento_Nubes":
            if gdal_file.RasterCount != 1:
                errors += "\t- Imagen con {} bandas, esperado 1 bandas\n".format(gdal_file.RasterCount)
        else:
            if gdal_file.RasterCount != 4:
                errors += "\t- Imagen con {} bandas, esperado 4 bandas\n".format(gdal_file.RasterCount)

        # check the data type
        # 1: "int8",
        dtype = {1: "uint8", 2: "uint16", 3: "int16", 4: "uint32", 5: "int32",
                 6: "float32", 7: "float64", 10: "complex64", 11: "complex128"}

        if img_file.endswith("Reflec_SR.tif"):
            if gdal_file.GetRasterBand(1).DataType not in [3, 5]:
                errors += "\t- Imagen con tipo de dato {}, esperado {}, {}\n".format(dtype[gdal_file.GetRasterBand(1).DataType], dtype[3], dtype[5])
        elif parent_dir != "6.2.Enmascaramiento_Nubes":
            if gdal_file.GetRasterBand(1).DataType not in [2, 4]:
                errors += "\t- Imagen con tipo de dato {}, esperado {}, {}\n".format(dtype[gdal_file.GetRasterBand(1).DataType], dtype[2], dtype[4])


        # pixel size
        pixel_size_x = abs(round(gdal_file.GetGeoTransform()[1], 3))
        pixel_size_y = abs(round(gdal_file.GetGeoTransform()[5], 3))
        if (pixel_size_x, pixel_size_y) != (30.0, 30.0):
            errors += "\t- Imagen con tamaño de pixel {}x{}, esperado 30.0x30.0\n".format(pixel_size_x, pixel_size_y)

        # check the projection
        parent_dir = os.path.basename(os.path.dirname(os.path.dirname(img_file)))
        if parent_dir == "3.2.1.Reflectancia_SR" or parent_dir == "6.2.Enmascaramiento_Nubes":
            try:
                filename = os.path.basename(img_file).split(".")[0]
                path = int(filename.split("_")[1])
                row = int(filename.split("_")[2])

                with rasterio.open(img_file) as src:
                    epsg = src.crs.to_epsg()

                if path in [3, 4, 5]:
                    if epsg != 32619:
                        errors += "\t- Imagen con sistema coordenadas {}, esperado {}\n".format(epsg, 32619)
                elif path in [6] and row in [55, 56, 57, 58]:
                    if epsg != 32619:
                        errors += "\t- Imagen con sistema coordenadas {}, esperado {}\n".format(epsg, 32619)
                elif path in [7] and row in [52]:
                    if epsg != 32619:
                        errors += "\t- Imagen con sistema coordenadas {}, esperado {}\n".format(epsg, 32619)
                elif path in [10] and row in [59]:
                    if epsg != 32617:
                        errors += "\t- Imagen con sistema coordenadas {}, esperado {}\n".format(epsg, 32617)
                elif path in [11] and row in [55]:
                    if epsg != 32617:
                        errors += "\t- Imagen con sistema coordenadas {}, esperado {}\n".format(epsg, 32617)
                else:
                    if epsg != 32618:
                        errors += "\t- Imagen con sistema coordenadas {}, esperado {}\n".format(epsg, 32618)
            except:
                errors += "\t- No se pudo verificar la proyeccion\n"

        if parent_dir == "3.2.2.Reflectancia_SR_Enmascarada" or parent_dir == "3.2.3.Reflectancia_Normalizada":
            try:
                with rasterio.open(img_file) as src:
                    epsg = src.crs.to_epsg()

                if epsg != 32618:
                    errors += "\t- Imagen con sistema coordenadas {}, esperado {}\n".format(epsg, 32618)
            except:
                errors += "\t- No se pudo verificar la proyeccion\n"

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
            if parent_dir == "6.2.Enmascaramiento_Nubes":
                ptype = filename.split("_")[5:6]
                if ptype != ["Mask"]: raise Exception("Archivo dentro de la carpeta '{}' debe finalizar con 'Mask'".format(parent_dir))

        except Exception as e:
            errors += "\t- Error en el nombre de la imagen: {}\n".format(e)

        # check enmask - mask
        try:
            filename = os.path.basename(img_file).split(".")[0]
            path = int(filename.split("_")[1])
            row = int(filename.split("_")[2])

            parent_dir = os.path.basename(os.path.dirname(os.path.dirname(img_file)))
            if parent_dir == "3.2.2.Reflectancia_SR_Enmascarada":
                mask_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(img_file))))),
                                         "6.Procesos_Mosaico_Anual", "6.2.Enmascaramiento_Nubes", "{}_{}".format(path, row),
                                         filename.split("Reflec_SR_Enmask")[0]+"Mask.tif")
                if not os.path.isfile(mask_path):
                    errors += "\t- Imagen enmascarada sin archivo de mascara, ruta de mascara esperada: {}\n".format(mask_path)
        except:
            errors += "\t- No se pudo verificar si existe la mascara para el archivo enmascarado\n"

        # statistics
        try:
            filename = os.path.basename(img_file).split(".")[0]
            parent_dir = os.path.basename(os.path.dirname(os.path.dirname(img_file)))
            path = int(filename.split("_")[1])
            row = int(filename.split("_")[2])
            if os.path.basename(os.path.dirname(img_file)) == "{}_{}".format(path, row):
                pair_path = parent_dir + "/" + "{}_{}".format(path, row)
                if pair_path not in num_files_in_path_row:
                    num_files_in_path_row[pair_path] = 1
                else:
                    num_files_in_path_row[pair_path] += 1
        except:
            pass

        # finally

        if errors != "":
            print("\nERRORES PARA: " + img_file + ":")
            print(errors)
            imgs_with_problems += 1

    print("\nEstadisticas de imagenes por cada path-row:")
    for path_row, num_files in num_files_in_path_row.items():
        print("\t{}: {}".format(path_row, num_files))

    print("\nDONE: Images with problems: {} of {}\n".format(imgs_with_problems, len(img_files)))


if __name__ == '__main__':
    script()
