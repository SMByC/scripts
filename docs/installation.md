# Installation

First define the path where save scripts:

```bash
export SCRIPTS_DIR="/path/to/dir"
```

Download from source:

```bash
hg clone https://bitbucket.org/smbyc/scripts $SCRIPTS_DIR
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
alias layer-stack="bash $SCRIPTS_DIR/scripts/layer-stack.sh"
```

## Pyramids

Create alias in bashrc:

```bash
export SCRIPTS_DIR="/path/to/dir"
alias pyramids="bash $SCRIPTS_DIR/scripts/pyramids.sh"
```