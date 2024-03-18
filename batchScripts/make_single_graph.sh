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
	8)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/synth1.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/synth1.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/synth1 -agg_func median;;
	8.1)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/synth2.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/synth2.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/synth2 -agg_func median;;
	8.2)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/naiv2.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/naiv2.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/naiv2 -agg_func median;;
	8.3)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/naiv3.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/naiv3.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/naiv3 -agg_func median;;
	8.4)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/diamond.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/diamond.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/diamond -agg_func median;;
	8.5)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/diamond_conf1.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/diamond_conf1.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/diamond_conf1 -agg_func median;;
	8.6)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/diamond_conf10.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/diamond_conf10.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/diamond_conf10 -agg_func median;;
	8.7)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/diamond_conf50.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/diamond_conf50.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/diamond_conf50 -agg_func median;;

esac

deactivate

