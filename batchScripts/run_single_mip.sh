#!/bin/bash
#SBATCH --time=0:05:00
#SBATCH --mail-user=mpha19@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=naples
#SBATCH --mem=8gb


FILENAME=$1
OUTPUT=$2
WAVELENGTHS=$3
DEMANDS=$4

cd ../src

# Create and activate a virtual environment
source venv/bin/activate

# Run your Python script
python mip.py --filename=$FILENAME --wavelengths=$WAVELENGTHS --demands=$DEMANDS > $OUTPUT

# Deactivate the virtual environment
deactivate
# Additional commands or post-processing can go here
exit