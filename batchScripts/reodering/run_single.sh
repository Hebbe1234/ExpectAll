#!/bin/bash
#SBATCH --time=8:00:00
#SBATCH --mail-user=frederikhyldgaard23@gmail.com
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=30G



FILENAME=$1
OUTPUT=$2
OTHER_ORDER=$2
GENERICS_FIRST=$2

cd ../../src

# Create and activate a virtual environment
source bdd_venv/bin/activate
output_file="../out/$OUTPUT/$FILENAME.txt"
# Run your Python script
python3 reordering.py --filename=$FILENAME --other_order=$OTHER_ORDER --generics_first=$GENERICS_FIRST > $output_file

# Deactivate the virtual environment
deactivate
# Additional commands or post-processing can go here
exit
