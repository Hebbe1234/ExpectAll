#!/bin/bash

# Configuration for Slurm job
#SBATCH --partition=dhabi
#SBATCH --mem=10G
#SBATCH --timeout=1:00:00


# Command-line arguments
command=$1
outdir=$2

# Setup output folder
mkdir -p ../$outdir/logs

# Change directory and activate virtual environment
cd ../src/mkplot 
source ../bdd_venv/bin/activate 

# Run your Python script
eval python3 -u $command > ../$outdir/logs/$job_id.txt


# Deactivate virtual environment
deactivate