#!/bin/bash
#SBATCH --time=0:05:00
#SBATCH --mail-user=rhebsg19@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=50G
#SBATCH --parsable


let "m=1024*1024*50"
ulimit -v $m

SRC=$1
TOPOLOGYPATH=$2
FILENAME=$3
OUTPUT=$4
WAVELENGTHS=$5
DEMANDS=$6
RUNFILE=$7
EXPERIMENT=$8

# Create and activate a virtual environment
source $SRC/bdd_venv/bin/activate
echo "${FILENAME};"
# Run your Python script
python3 -u $SRC/$RUNFILE --experiment=$EXPERIMENT --filename=$TOPOLOGYPATH$FILENAME --wavelengths=$WAVELENGTHS --demands=$DEMANDS > $OUTPUT


# Deactivate the virtual environment
deactivate



# Additional commands or post-processing can go here
exit
