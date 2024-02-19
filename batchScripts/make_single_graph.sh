#!/bin/bash

#SBATCH --mail-user=fhyldg18@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=10G

graph=$1
out=$2

cd ../src/mkplot
source ../bdd_venv/bin/activate


case $graph in
	0.1)
		python3 ../src/mkplot/make_cactus.py --dirs $out split_fancy3.tar.gz --xaxis 0 0 --legend new old --savedest ./cactus_graphs/superscript
esac

deactivate

