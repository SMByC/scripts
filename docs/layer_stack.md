## Layer stack

There are two script for make the layer stack:

### Individually

Make the layerstack for all images in the input order, the output file has inside the separate images stack as image1, image2, ... imageN

#### How to use

##### Command line:

In shell application go to directory where are the files and execute:

```bash
layer-stack image1 image2 ... imageN
```

The output is a Geotiff image named *_allbands.tif

### Bulk for Landsat

Make the default (Reflec SR) layer stack for all landsat folders in current directory

#### How to use

##### Command line:

In shell application go to directory where are the decompressed Landsat folders and execute:

```bash
layer-stack-bulk
```

The script search all folders start with _L*_ such as _LT050030592006031301T1_ and make the layer stack using by default the bands _1,2,3,4,5,7_, if you want change the bands for the layer stack run with _-b_ option thus:

```bash
layer-stack-bulk -b=3,4,5
```

The layerstack output is saved in the same directory where the script is executed ending with _"Reflec_SR.tif"_