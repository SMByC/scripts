## Check images

Checking the structure and integrity of the Landsat files under the SMByC guidelines.

Checks:

 + It's not a corrupt file
 + Have 4 bands
 + Data type in uint16 or uint32
 + EPSG in 32618
 + Pixel size 30x30
 + Check SMByC finename
 + Check if the file is in the correct parent directory

### How to use

#### Check all images in the current directory

In shell application go to directory where are the files or dirs, this check all images in all sub-directories of the current directory:

```bash
check-imgs
```

#### Check a specific directory/files

```bash
check-imgs DIR_OR_FILES
```

#### Save the output

If the script show a several checks, you can save in a text file all outputs of the script with the following command:

```bash
check-imgs > check_imgs.txt
```
