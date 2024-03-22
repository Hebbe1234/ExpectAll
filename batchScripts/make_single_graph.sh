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
	6.3)
		python3 make_cactus.py --dirs  rsa_inc_par_martin rsa_lim_martin rsa_inc_par_lim_martin rsa_baseline.tar.gz --xaxis 0 0 0 0  --legend inc_par lim inc_par_lim baseline --savedest ./cactus_graphs/rsa_inc_par_vs_baseline;;
	7.1)
		python3 make_cactus.py --dirs  rsa_seq_martin rsa_inc_par_seq_martin rsa_baseline.tar.gz --xaxis 0 0 0  --legend seq inc_par_seq baseline --savedest ./cactus_graphs/rsa_inc_seq_vs_baseline;;
	8.1)
		python3 make_cactus.py --dirs  sequential_P2_v22 rsa_baseline.tar.gz --xaxis 0 0  --legend seq baseline --savedest ./cactus_graphs/rsa_seq_vs_baseline;;
	411.0)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/$out.csv -yfill 3600;
        python3 AAU_scatter.py -d csv/$out.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/$out -agg_func median;;
	411.1)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/$out.csv -yfill 3600;
        python3 AAU_scatter.py -d csv/$out.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/$out -agg_func median;;
esac

deactivate

