#!/bin/bash
job_id=$SLURM_JOB_ID

let "m=1024*1024*50"
ulimit -v $m

args=("$@")
outdir=${args[-1]}
# Remove the last argument from the array
unset 'args[${#args[@]}-1]' 

# Setup output folder
mkdir -p $outdir/logs
mkdir -p $outdir/results

# Create and activate a virtual environment
source ../src/bdd_venv/bin/activate

# Run your Python script
python3 -u "${args[@]}" --result_output="$outdir/results/$job_id.json" --bdd_output="$outdir/results/$job_id.json" --replication_output_file_prefix="$outdir/results/$job_id"  > $outdir/logs/$job_id.txt

# Deactivate the virtual environment
deactivate



# Additional commands or post-processing can go here
exit
