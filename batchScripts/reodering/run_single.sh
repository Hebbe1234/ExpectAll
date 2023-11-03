#!/bin/bash
#SBATCH --time=8:00:00
#SBATCH --mail-user=frederikhyldgaard23@gmail.com
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=10G



FILENAME=$1
OUTPUT=$2

cd ../../src

# Create and activate a virtual environment
source bdd_venv/bin/activate
output_file="../out/$OUT/$FILENAME.txt"
# Run your Python script
python3 reordering.py --filename=$FILENAME > $output_file

# Deactivate the virtual environment
deactivate
# Additional commands or post-processing can go here
exit
