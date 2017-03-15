# Scripts

Here there are some scripts with different purpose oriented to process raster images. This scripts mainly tested with Landsat images and Linux.

## Rename Landsat files

Rename Landsat images files from, e.g:

    LE70080532002152EDC00SR_Enmask.tif 

to standard structure of SMByC project:

    Landsat_8_53_020601_7ETM_Reflec_SR_Enmask.tif

**How to use**

Command line:

```bash
rename-landsat-files -t TYPE DIR_OR_FILES
```

  - `-t` TYPE
    - rename type
    - options: reflec, mask, enmask, mtl, norm, aefectiva, compuesto
  - `DIR_OR_FILES`
    - directories or images files to process, it search recursively all images files in the directories, such as: tif, img, aux, rdd

Run as script:

  - First edit the file script in the two lines:
    - `type_rename =` options: reflec, mask, enmask, mtl, norm, aefectiva, compuesto
    - `dir_files =` directories or images files to process, it search recursively all images files in the directories, such as: tif, img, aux, rdd

  - Run script in python environment

## Layer stack

Make the layerstack for all images in the input order:

```bash
layer-stack image1 image2 ... imageN
```

The output is a Geotiff image named *_allbands.tif with separate images stack as image1, image2, ... imageN

## Pyramids

Compute the pyramids inside the tif image (with compression):

```bash
pyramids image.tif
```

First it compress the image (with deflate compression) and then compute the pyramids in the levels: 2 4 6 8 12 16 24 32. It save the pyramids inside the tif and overwrite the input file, and is possible pass more than one images for compute the pyramids (such as pyramids img1.tif img2.tif ... )

