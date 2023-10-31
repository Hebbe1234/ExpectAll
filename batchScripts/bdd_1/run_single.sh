#!/bin/bash
#SBATCH --time=0:20:00
#SBATCH --mail-user=frederikhyldgaard23@gmail.com
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=50G


FILENAME=$1
OUTPUT=$2
WAVELENGTHS=$3
DEMANDS=$4

cd ../../src

# Create and activate a virtual environment
source bdd_venv/bin/activate

# Run your Python script
python3 run_bdd.py --filename=$FILENAME --wavelengths=$WAVELENGTHS --demands=$DEMANDS > $OUTPUT

# Deactivate the virtual environment
deactivate
# Additional commands or post-processing can go here
exit
