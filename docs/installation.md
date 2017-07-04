# Installation

First define the path where save scripts:

```bash
export SCRIPTS_DIR="/path/to/dir"
```

Download from source:

```bash
hg clone https://bitbucket.org/smbyc/scripts $SCRIPTS_DIR
```

## Extract the landsat files

Create alias in bashrc:

```bash
export SCRIPTS_DIR="/path/to/dir"
alias extract-landsat-files="bash $SCRIPTS_DIR/scripts/extract_landsat_files.sh"
```

## Rename Landsat files

Create alias in bashrc:

```bash
export SCRIPTS_DIR="/path/to/dir"
alias rename-landsat-files="python $SCRIPTS_DIR/scripts/rename_landsat_files.py"
```

## Layer stack

Create alias in bashrc:

```bash
export SCRIPTS_DIR="/path/to/dir"
alias layer-stack="bash $SCRIPTS_DIR/scripts/layer_stack.sh"
alias layer-stack-bulk="bash $SCRIPTS_DIR/scripts/layer_stack_bulk.sh"
```

## Pyramids

Create alias in bashrc:

```bash
export SCRIPTS_DIR="/path/to/dir"
alias pyramids="bash $SCRIPTS_DIR/scripts/pyramids.sh"
```