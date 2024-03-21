#!/bin/bash

#SBATCH --mail-user=fhyldg18@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=dhabi
#SBATCH --mem=10G

graph=$1
out=$2
seed=$3
cd ../src/mkplot
source ../bdd_venv/bin/activate
######## THE CSV VARIES BASED ON IT BEING A BDD OR A MIP SOLUTION !!!!! CAUTION

case $graph in
	0.1)
		python3 make_cactus.py --dirs $out split_fancy3.tar.gz --xaxis 0 0 --legend new old --savedest ./cactus_graphs/superscript;;
	
	250)
		python3 convert_to_csv.py -dir ../../out/mip_limited_n_demands_dt_2_paths5 -x 5 -savedest csv/mip_limited_n_demands_dt_2_paths5.csv -yfill 3600;
        python3 AAU_scatter.py -d csv/mip_limited_n_demands_dt_2_paths5.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/mip_limited_n_demands_dt_2_paths5 -agg_func median;;

	350)
		python3 convert_to_csv.py -dir ../../out/mip_limited_n_demands_kanto_2_paths5 -x 5 -savedest csv/mip_limited_n_demands_kanto_2_paths5.csv -yfill 3600;
        python3 AAU_scatter.py -d csv/mip_limited_n_demands_kanto_2_paths5.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/mip_limited_n_demands_kanto_2_paths5 -agg_func median;;


	
	500)
		python3 convert_to_csv.py -dir ../../out/mip_limited_n_demands_2_paths_dt${out}3 -x 5 -savedest csv/mip_limited_n_demands_2_paths_dt${out}3.csv -yfill 3600;
        python3 AAU_scatter.py -d csv/mip_limited_n_demands_2_paths_dt${out}3.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/mip_limited_n_demands_2_paths_dt${out}3 -agg_func median;;
	600)

		python3 convert_to_csv.py -dir ../../out/mip_limited_n_demands_2_paths_kanto${out}2 -x 5 -savedest csv/mip_limited_n_demands_2_paths_kanto${out}2.csv -yfill 3600;
        python3 AAU_scatter.py -d csv/mip_limited_n_demands_2_paths_kanto${out}2.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/mip_limited_n_demands_2_paths_kanto${out}2 -agg_func median;;

	5.1)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/dt_2_path$seed.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/dt_2_path$seed.csv -xlabel Demands -ylabel "Run time (s)" -agg 2 -x 4 -savedest new_graphs/dt_2_path$seed -agg_func median;;
	5.2)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/kanto_2_path$seed.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/kanto_2_path$seed.csv -xlabel Demands -ylabel "Run time (s)" -agg 2 -x 4 -savedest new_graphs/kanto_2_path$seed -agg_func median;;

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
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/diamond_conf_1.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/diamond_conf_1.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/diamond_conf_1 -agg_func median;;
	8.6)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/diamond_conf_10.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/diamond_conf_10.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/diamond_conf_10 -agg_func median;;
	8.7)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/diamond_conf_50.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/diamond_conf_50.csv -xlabel Demands -ylabel "Run time (s)" -agg 0 -x 5 -savedest new_graphs/diamond_conf_50 -agg_func median;;


	9)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/mip_lim_dt2.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/mip_lim_dt2.csv -xlabel Demands -ylabel "Run time (s)" -agg 2 -x 4 -savedest new_graphs/mip_lim_dt2 -agg_func median;;
	9.1)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/mip_lim_kanto2.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/mip_lim_kanto2.csv -xlabel Demands -ylabel "Run time (s)" -agg 2 -x 4 -savedest new_graphs/mip_lim_kanto2 -agg_func median;;
	9.2)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/mip_dt2.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/mip_dt2.csv -xlabel Demands -ylabel "Run time (s)" -agg 2 -x 4 -savedest new_graphs/mip_dt2 -agg_func median;;
	9.3)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/mip_kanto2.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/mip_kanto2.csv -xlabel Demands -ylabel "Run time (s)" -agg 2 -x 4 -savedest new_graphs/mip_kanto2 -agg_func median;;
	
	9.4)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/mip_dt_2_path.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/mip_dt_2_path.csv -xlabel Demands -ylabel "Run time (s)" -agg 2 -x 4 -savedest new_graphs/mip_dt_2_path -agg_func median;;
	9.5)
		python3 convert_to_csv.py -dir ../../out/$out -x 5 -savedest csv/mip_kanto_2_path.csv -yfill 3600;
		python3 AAU_scatter.py -d csv/mip_kanto_2_path.csv -xlabel Demands -ylabel "Run time (s)" -agg 2 -x 4 -savedest new_graphs/mip_kanto_2_path -agg_func median;;

esac

deactivate

