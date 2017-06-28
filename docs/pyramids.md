## Pyramids

Compute the pyramids inside the tif image (with compression).

First it compress the image (with deflate compression) and then compute the pyramids in the levels: 2 4 6 8 12 16 24 32. It save the pyramids inside the tif and overwrite the input file.

### How to use

#### Command line:

In shell application go to directory where are the files and execute:

```bash
pyramids image.tif
```

Is possible pass more than one images for compute the pyramids (e.g. pyramids img1.tif img2.tif img3.tif)
