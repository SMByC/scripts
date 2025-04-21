import os
import argparse
from osgeo import gdal


def compress_geotiff(input_file, output_file):
    """
    Compress a GeoTIFF file using GDAL with specified options.

    Args:
        input_file (str): Path to the input GeoTIFF file
        output_file (str): Path to the output compressed GeoTIFF file
    """
    # GDAL translate options
    translate_options = gdal.TranslateOptions(
        format='GTiff',
        creationOptions=[
            'COMPRESS=LZW',
            'PREDICTOR=2',
            'BIGTIFF=YES'
        ]
    )

    # Perform the compression
    gdal.Translate(output_file, input_file, options=translate_options)
    print(f"Compressed GeoTIFF saved as: {output_file}")


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Compress a GeoTIFF file using GDAL.')
    parser.add_argument('input_file', help='Path to the input GeoTIFF file')
    parser.add_argument('output_file', help='Path to the output compressed GeoTIFF file')

    # Parse arguments
    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file {args.input_file} does not exist")
        return

    # Run compression
    compress_geotiff(args.input_file, args.output_file)


if __name__ == '__main__':
    main()