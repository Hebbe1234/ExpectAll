#!/bin/bash

#SBATCH --mail-user=fhyldg18@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=naples
#SBATCH --mem=10G

graph=$1
out=$2

cd ../src/mkplot
source ../bdd_venv/bin/activate


case $graph in
	0.1)
		python3 make_cactus.py --dirs $out split_fancy3.tar.gz --xaxis 0 0 --legend new old --savedest ./cactus_graphs/superscript;;
	0.2)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/one_path_kanto.csv -yfill 3600;
        python3 AAU_scatter.py -d csv/one_path_kanto.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/one_path_kanto -agg_func median;;
	0.3)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/one_path_dt.csv -yfill 3600;
        python3 AAU_scatter.py -d csv/one_path_dt.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/one_path_dt -agg_func median;;
	0.4)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/one_path_kanto_more_demands.csv -yfill 3600;
        python3 AAU_scatter.py -d csv/one_path_kanto_more_demands.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/one_path_kanto_more_demands -agg_func median;;

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

esac

deactivate

