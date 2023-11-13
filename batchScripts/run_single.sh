#!/bin/bash
#SBATCH --time=0:40:00
#SBATCH --mail-user=fhyldg18@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=50G

let "m=1024*1024*35"
ulimit -v $m

SRC=$1
FILENAME=$2
OUTPUT=$3
WAVELENGTHS=$4
DEMANDS=$5
RUNFILE=$6
EXPERIMENT=$7

# Create and activate a virtual environment
source $SRC/bdd_venv/bin/activate

# Run your Python script
python3 $SRC/$RUNFILE --experiment=$EXPERIMENT --filename=$FILENAME --wavelengths=$WAVELENGTHS --demands=$DEMANDS > $OUTPUT


# Deactivate the virtual environment
deactivate
# Additional commands or post-processing can go here
exit
