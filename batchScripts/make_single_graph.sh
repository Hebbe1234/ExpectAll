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
		python3 make_cactus.py --dirs $out split_fancy3.tar.gz --xaxis 0 0 --legend new old --savedest ./cactus_graphs/superscript;;

	6)
		python3 make_cactus.py --dirs $out rsa_baseline.tar.gz --xaxis 0 0 --legend rsa_inc_par_lim rsa_baseline --savedest ./cactus_graphs/rsa_inc_par_lim_vs_baseline;;
	6.1)
		python3 make_cactus.py --dirs $out rsa_baseline.tar.gz --xaxis 0 0 --legend rsa_lim 		rsa_baseline --savedest ./cactus_graphs/rsa_lim_vs_baseline;;
	6.2)
		python3 make_cactus.py --dirs $out rsa_baseline.tar.gz --xaxis 0 0 --legend rsa_inc_par 	rsa_baseline --savedest ./cactus_graphs/rsa_inc_par_vs_baseline;;


esac

deactivate

