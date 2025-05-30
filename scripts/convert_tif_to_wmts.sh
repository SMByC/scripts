#!/bin/bash

# Function to display usage information
show_usage() {
    echo "Usage: $0 [OPTIONS] input.tif"
    echo
    echo "Convert a GeoTIFF file to Web Map Tile Service (WMTS) format."
    echo
    echo "Options:"
    echo "  -h, --help                 Show this help message and exit"
    echo "  -o, --output-dir DIR       Set output base directory (default: current directory)"
    echo "  -n, --min-zoom LEVEL       Set minimum zoom level (default: 0)"
    echo "  -x, --max-zoom LEVEL       Set maximum zoom level (default: 16)"
    echo "  -u, --url-base URL         Set base URL for tiles (default: file:///Z:/WMTS/)"
    echo "  -f, --format FORMAT        Set tile format (webp, png, jpeg) (default: webp)"
    echo "  -q, --quality VALUE        Set quality for lossy formats (0-100) (default: 95)"
    echo "  -l, --lossless             Use lossless compression for WEBP (default: enabled)"
    echo "  -p, --processes NUM        Number of parallel processes (default: 12)"
    echo "  -r, --resampling METHOD    Resampling method (near, bilinear, cubic, etc.) (default: near)"
    echo
    echo "Example:"
    echo "  $0 -o /path/to/output -n 2 -x 15 -f png input.tif"
}

# Default values
OUTPUT_BASEDIR="/home/smbyc/cona3/WMTS"
MIN_ZOOM=0
MAX_ZOOM=16
SOURCE_URL_BASE="file:///Z:/WMTS/"
TILE_FORMAT="webp"
QUALITY=95
LOSSLESS=true
PROCESSES=12
RESAMPLING="near"

# Parse command line arguments
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -o|--output-dir)
            OUTPUT_BASEDIR="$2"
            shift 2
            ;;
        -n|--min-zoom)
            MIN_ZOOM="$2"
            shift 2
            ;;
        -x|--max-zoom)
            MAX_ZOOM="$2"
            shift 2
            ;;
        -u|--url-base)
            SOURCE_URL_BASE="$2"
            shift 2
            ;;
        -f|--format)
            TILE_FORMAT="$2"
            shift 2
            ;;
        -q|--quality)
            QUALITY="$2"
            shift 2
            ;;
        -l|--lossless)
            LOSSLESS=true
            shift
            ;;
        -p|--processes)
            PROCESSES="$2"
            shift 2
            ;;
        -r|--resampling)
            RESAMPLING="$2"
            shift 2
            ;;
        -*|--*)
            echo "Error: Unknown option $1"
            show_usage
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

# Restore positional parameters
set -- "${POSITIONAL_ARGS[@]}"

# Check if input file is provided
if [ "$#" -ne 1 ]; then
    echo "Error: Input file is required."
    show_usage
    exit 1
fi

INPUT_FILE="$1"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' does not exist."
    exit 1
fi

# Check if input file is readable
if [ ! -r "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' is not readable."
    exit 1
fi

# Check if output directory is writable
if [ ! -w "$(dirname "$OUTPUT_BASEDIR")" ]; then
    echo "Error: Output directory '$(dirname "$OUTPUT_BASEDIR")' is not writable."
    exit 1
fi

# Validate zoom levels
if ! [[ "$MIN_ZOOM" =~ ^[0-9]+$ ]] || ! [[ "$MAX_ZOOM" =~ ^[0-9]+$ ]]; then
    echo "Error: Zoom levels must be non-negative integers."
    exit 1
fi

if [ "$MIN_ZOOM" -gt "$MAX_ZOOM" ]; then
    echo "Error: Minimum zoom level cannot be greater than maximum zoom level."
    exit 1
fi

# Validate tile format
case "$TILE_FORMAT" in
    webp|png|jpeg)
        ;;
    *)
        echo "Error: Unsupported tile format '$TILE_FORMAT'. Supported formats: webp, png, jpeg."
        exit 1
        ;;
esac

# Validate quality
if ! [[ "$QUALITY" =~ ^[0-9]+$ ]] || [ "$QUALITY" -lt 0 ] || [ "$QUALITY" -gt 100 ]; then
    echo "Error: Quality must be an integer between 0 and 100."
    exit 1
fi

# Validate processes
if ! [[ "$PROCESSES" =~ ^[0-9]+$ ]] || [ "$PROCESSES" -lt 1 ]; then
    echo "Error: Number of processes must be a positive integer."
    exit 1
fi

# Set up layer name and output directory
LAYER_NAME=$(basename "$INPUT_FILE" .tif)
OUTPUT_DIR="$OUTPUT_BASEDIR/$LAYER_NAME"

# Set up source URL
SOURCE_URL="$SOURCE_URL_BASE$LAYER_NAME/{z}/{x}/{-y}.$TILE_FORMAT"

# Create temporary directory for intermediate files
TEMP_DIR=$(mktemp -d)
if [ $? -ne 0 ]; then
    echo "Error: Failed to create temporary directory."
    exit 1
fi

# Function to clean up temporary files
cleanup() {
    echo "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
    exit $1
}

# Set up trap to clean up on exit
trap 'cleanup 1' INT TERM

# Check for required tools
echo "Checking for required tools..."
for cmd in gdalinfo gdal_translate gdal_merge.py gdalwarp gdal2tiles.py; do
  if ! command -v $cmd &> /dev/null; then
    echo "Error: $cmd is not installed or not in PATH."
    cleanup 1
  fi
done

# Check for color table and band count
echo "Analyzing input file..."
BAND_COUNT=$(gdalinfo "$INPUT_FILE" | grep -c "^Band ")
IS_PALETTED=$(gdalinfo "$INPUT_FILE" | grep -c "Color Table")

# Step 1: Convert to RGB if needed
TEMP_TIF="$TEMP_DIR/$(basename "$INPUT_FILE" .tif)_rgb.tif"

if [ "$IS_PALETTED" -gt 0 ]; then
  echo "Paletted raster detected. Expanding to RGB..."
  gdal_translate -ot Byte -expand rgba "$INPUT_FILE" "$TEMP_TIF"
elif [ "$BAND_COUNT" -eq 1 ]; then
  echo "Grayscale raster detected. Converting to RGB..."
  TEMP_GRAY="$TEMP_DIR/tmp_gray_byte.tif"
  gdal_translate -ot Byte -scale "$INPUT_FILE" "$TEMP_GRAY"
  gdal_merge.py -separate -o "$TEMP_TIF" "$TEMP_GRAY" "$TEMP_GRAY" "$TEMP_GRAY"
  rm -f "$TEMP_GRAY"
else
  echo "Multi-band raster detected. Converting to 8-bit RGB..."
  gdal_translate -ot Byte -scale "$INPUT_FILE" "$TEMP_TIF"
fi

# Create output directory if it doesn't exist
if [ ! -d "$OUTPUT_DIR" ]; then
  echo "Creating output directory: $OUTPUT_DIR"
  mkdir -p "$OUTPUT_DIR"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to create output directory."
    cleanup 1
  fi
fi

# Set up tile format options
TILE_OPTIONS=""
case "$TILE_FORMAT" in
  webp)
    TILE_OPTIONS="--tiledriver=WEBP --webp-quality=$QUALITY"
    if [ "$LOSSLESS" = true ]; then
      TILE_OPTIONS="$TILE_OPTIONS --webp-lossless"
    fi
    ;;
  png)
    TILE_OPTIONS="--tiledriver=PNG"
    ;;
  jpeg)
    TILE_OPTIONS="--tiledriver=JPEG --jpeg-quality=$QUALITY"
    ;;
esac

# Generate tiles
echo "Generating XYZ WMTS tiles in EPSG:3857..."
echo "  Zoom levels: $MIN_ZOOM to $MAX_ZOOM"
echo "  Format: $TILE_FORMAT"
echo "  Resampling method: $RESAMPLING"
echo "  Parallel processes: $PROCESSES"
echo "  Output directory: $OUTPUT_DIR"

# Build the gdal2tiles.py command
GDAL2TILES_CMD="gdal2tiles.py \
  -z $MIN_ZOOM-$MAX_ZOOM \
  --profile mercator \
  --resampling $RESAMPLING \
  $TILE_OPTIONS \
  --processes=$PROCESSES \
  -t \"$LAYER_NAME\" \
  -c \"SMByC\" \
  \"$TEMP_TIF\" \
  \"$OUTPUT_DIR\""

# Execute the command
eval $GDAL2TILES_CMD

# Check if the command was successful
if [ $? -ne 0 ]; then
  echo "Error: Failed to generate tiles."
  cleanup 1
fi

##### QGIS Layer Definition File (.qlr)

# Function to URL encode a string
urlencode() {
  local str="$1"
  local length="${#str}"
  local encoded=""
  for (( i = 0; i < length; i++ )); do
    local c="${str:$i:1}"
    case "$c" in
      [a-zA-Z0-9.~_-]|:|/|\\) encoded+="$c" ;;
      *) printf -v hex '%%%02X' "'$c"
         encoded+="$hex"
         ;;
    esac
  done
  echo "$encoded"
}

# Generate a QGIS Layer Definition File
echo "Generating QGIS Layer Definition File (.qlr)..."

# Check if uuidgen is available
if ! command -v uuidgen &> /dev/null; then
  echo "Warning: uuidgen is not installed. Using a random ID instead."
  LAYER_ID="layer_$(date +%s)_$RANDOM"
else
  LAYER_ID=$(uuidgen)
fi

OUTPUT_QLR_FILE="$OUTPUT_DIR/$(basename "$INPUT_FILE" .tif).qlr"

# Create the QLR content
cat > "$OUTPUT_QLR_FILE" << EOF
<!DOCTYPE qgis-layer-definition>
<qlr>
  <layer-tree-group groupLayer="" expanded="1" name="" checked="Qt::Checked">
  <customproperties>
    <Option/>
  </customproperties>
    <layer-tree-layer source="type=xyz&amp;url=$(urlencode "$SOURCE_URL")&amp;zmax=$MAX_ZOOM&amp;zmin=$MIN_ZOOM" providerKey="wms" expanded="1" checked="Qt::Checked" id="$LAYER_ID" name="$LAYER_NAME">
    <customproperties>
      <Option/>
    </customproperties>
  </layer-tree-layer>
  </layer-tree-group>
  <maplayers>
    <maplayer autoRefreshTime="0" refreshOnNotifyMessage="" autoRefreshMode="Disabled" legendPlaceholderImage="" minScale="1e+08" hasScaleBasedVisibilityFlag="0" refreshOnNotifyEnabled="0" maxScale="0" styleCategories="AllStyleCategories" type="raster">
      <id>$LAYER_ID</id>
      <datasource>type=xyz&amp;url=$(urlencode "$SOURCE_URL")&amp;zmax=$MAX_ZOOM&amp;zmin=$MIN_ZOOM</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>$LAYER_NAME</layername>
      <srs>
        <spatialrefsys>
          <wkt>PROJCRS["WGS 84 / Pseudo-Mercator",BASEGEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4326]],CONVERSION["Popular Visualisation Pseudo-Mercator",METHOD["Popular Visualisation Pseudo Mercator",ID["EPSG",1024]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["easting (X)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["northing (Y)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Web mapping and visualisation."],AREA["World between 85.06°S and 85.06°N."],BBOX[-85.06,-180,85.06,180]],ID["EPSG",3857]]</wkt>
          <proj4>+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs</proj4>
          <srsid>3857</srsid>
          <srid>3857</srid>
          <authid>EPSG:3857</authid>
          <description>WGS 84 / Pseudo-Mercator</description>
          <projectionacronym>merc</projectionacronym>
          <ellipsoidacronym>WGS84</ellipsoidacronym>
          <geographicflag>false</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <contact>
          <name></name>
          <organization></organization>
          <position></position>
          <voice></voice>
          <fax></fax>
          <email></email>
          <role></role>
        </contact>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>true</geographicflag>
          </spatialrefsys>
        </crs>
        <extent>
          <spatial dimensions="2" crs="" minx="0" miny="0" maxx="0" maxy="0"/>
          <temporal>
            <period>
              <start></start>
              <end></end>
            </period>
          </temporal>
        </extent>
      </resourceMetadata>
      <provider>wms</provider>
      <noData>
        <noDataList bandNo="1" useSrcNoData="0"/>
      </noData>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
        <Private>0</Private>
      </flags>
      <temporal enabled="0" mode="0" fetchMode="0">
        <fixedRange>
          <start></start>
          <end></end>
        </fixedRange>
      </temporal>
      <customproperties>
        <property key="identify/format" value="Undefined"/>
      </customproperties>
      <blendMode>0</blendMode>
    </maplayer>
  </maplayers>
</qlr>
EOF

# Check if the QLR file was created successfully
if [ ! -f "$OUTPUT_QLR_FILE" ]; then
  echo "Warning: Failed to create QGIS Layer Definition File."
else
  echo "QGIS Layer Definition File created: $OUTPUT_QLR_FILE"
fi

# Write the SOURCE_URL to xyz_url.txt file
OUTPUT_URL_FILE="$OUTPUT_DIR/xyz_url.txt"
echo "$SOURCE_URL" > "$OUTPUT_URL_FILE"
if [ ! -f "$OUTPUT_URL_FILE" ]; then
  echo "Warning: Failed to create xyz_url.txt file."
else
  echo "XYZ URL file created: $OUTPUT_URL_FILE"
fi

# Clean up temporary files
cleanup 0

# Print summary
echo
echo "=== Conversion Summary ==="
echo "Input file: $INPUT_FILE"
echo "Output directory: $OUTPUT_DIR"
echo "Tile format: $TILE_FORMAT"
echo "Zoom levels: $MIN_ZOOM to $MAX_ZOOM"
echo "URL for QGIS: $SOURCE_URL"
echo
echo "To use in QGIS, open the .qlr file: $OUTPUT_QLR_FILE"
echo "Done! Tiles are available in: $OUTPUT_DIR"
