#!/bin/bash

# Configuration for Slurm job
#SBATCH --mail-user=fhyldg18@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=10G

# Command-line arguments
graph=$1
out=$2

# Define common function to convert to CSV and plot scatter graphs
convert_and_plot() {
    local input_dir="../../out/$1"
    local output_csv="csv/$1.csv"
    python3 convert_to_csv.py -dir "$input_dir" -x 5 -savedest "$output_csv" -yfill 3600
    python3 AAU_scatter.py -d "$output_csv" -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest "new_graphs/$1" -agg_func median
}

# Change directory and activate virtual environment
cd ../src/mkplot 
source ../bdd_venv/bin/activate 

# Execute Python scripts based on the value of $graph
case $graph in
    0.1)
        python3 make_cactus.py --dirs "$out" --xaxis 0 --legend new --savedest ./cactus_graphs/superscript ;;
    0.2|0.3|0.4|0.5|0.6|0.7|0.8|411.0|411.1)
        convert_and_plot "$out" ;;
    200)
        convert_and_plot "one_path_kanto_more_demands${out}12" ;;
    300)
        convert_and_plot "one_path_dt_more_demands${out}12" ;;
    6|6.1|6.2|6.3)
        python3 make_cactus.py --dirs "$out" rsa_baseline.tar.gz --xaxis 0 0 --legend rsa_inc_par_lim rsa_baseline --savedest ./cactus_graphs/rsa_inc_par_lim_vs_baseline ;;
    7.1)
        python3 make_cactus.py --dirs rsa_seq_martin rsa_inc_par_seq_martin rsa_baseline.tar.gz --xaxis 0 0 0 --legend seq inc_par_seq baseline --savedest ./cactus_graphs/rsa_inc_seq_vs_baseline ;;
    8.1)
        python3 make_cactus.py --dirs sequential_P2_v22 rsa_baseline.tar.gz --xaxis 0 0 --legend seq baseline --savedest ./cactus_graphs/rsa_seq_vs_baseline ;;
    *)
        echo "Unsupported graph value: $graph" ;;
esac

# Deactivate virtual environment
deactivate