#!/bin/bash
#SBATCH --time=8:00:00
#SBATCH --mail-user=fhyldg18@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=50G



FILENAME=$1
OUTPUT=$2
OTHER_ORDER=$3
GENERICS_FIRST=$4
PREFIX=$5

cd ../../src



# Create and activate a virtual environment
source bdd_venv/bin/activate
output_file="../out/$OUTPUT/${PREFIX}_${FILENAME}.txt"
# Run your Python script
python3 -u reordering.py --filename=$FILENAME --other_order=$OTHER_ORDER --generics_first=$GENERICS_FIRST > $output_file

# Deactivate the virtual environment
deactivate
# Additional commands or post-processing can go here
exit
