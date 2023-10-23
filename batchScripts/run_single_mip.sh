#!/bin/bash
#SBATCH --time=0:05:00
#SBATCH --mail-user=mpha19@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=naples
#SBATCH --mem=15000
FILENAME=$1
WAVELENGTHS=$2
DEMANDS=$3
# Create and activate a virtual environment
source venv/bin/activate

#insert cd

# Run your Python script
python mip.py --filename=$FILENAME --wavelengths=$WAVELENGTHS --demands=$DEMANDS > "output.txt"
# Deactivate the virtual environment
deactivate
# Additional commands or post-processing can go here
exit