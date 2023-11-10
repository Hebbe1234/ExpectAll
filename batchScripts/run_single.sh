#!/bin/bash
#SBATCH --time=0:20:00
#SBATCH --mail-user=fhyldg18@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=50G

let "m=1024*1024*50"
ulimit -v $m

FILENAME=$1
OUTPUT=$2
WAVELENGTHS=$3
DEMANDS=$4
RUNFILE=$5
EXPERIMENT=$6
TOGRAPH=$7

cd ../src

# Create and activate a virtual environment
source bdd_venv/bin/activate

# Run your Python script
python3 $RUNFILE --experiment=$EXPERIMENT --filename=$FILENAME --wavelengths=$WAVELENGTHS --demands=$DEMANDS > $OUTPUT

cd mkplot




python3 AAU_create_json_and_make_pdfs.py $TOGRAPH 

# Deactivate the virtual environment
deactivate
# Additional commands or post-processing can go here
exit
