## Rename Landsat files

Rename Landsat images files from, e.g:

    LE70080532002152EDC00SR_Enmask.tif 

to standard structure of SMByC project:

    Landsat_8_53_020601_7ETM_Reflec_SR.tif

The SMByC filename structure is:

    Landsat_PP_RR_YYMMDD_VSSS_TYPE.tif

- PP: path
- RR: row
- YY: year
- MM: month
- DD: day
- V: landsat version
- SSS: sensor
- TYPE: rename type

Accept two filename format input:

* Old/Raw format e.g. _LC80070592016320LGN00_Enmask.tif_
* New (ESPA) format e.g. _LC08_L1TP_007059_20161115_20170318_01_T2_Enmask.tif_

### How to use

#### Command line (recommended):

In shell application go to directory where are the files and execute:

```bash
rename-landsat-files -t TYPE DIR_OR_FILES
```

  - `-t` TYPE
    - rename type
    - options: reflec, mask, enmask, mtl, norm, aefectiva, compuesto
  - `DIR_OR_FILES`
    - directories or images files to process, it search recursively all images files in the directories, such as: tif, img, aux, rdd

#### Run as script:

  - First edit the file script in the two lines:
    - `type_rename =` options: reflec, mask, enmask, mtl, norm, aefectiva, compuesto
    - `dir_files =` directories or images files to process, it search recursively all images files in the directories, such as: tif, img, aux, rdd

  - Run script in python environment