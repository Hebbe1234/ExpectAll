#!/bin/bash

# Configuration for Slurm job
#SBATCH --mail-user=fhyldg18@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=10G

# Command-line arguments
args=("$@")
outdir=${args[-1]}
# Remove the last argument from the array
unset 'args[${#args[@]}-1]' 

# Setup output folder
mkdir -p ../$outdir/logs

# Change directory and activate virtual environment
cd ../src/mkplot 
source ../bdd_venv/bin/activate 

# Run your Python script
python3 -u "${args[@]}" > ../$outdir/logs/$job_id.txt


# Deactivate virtual environment
deactivate