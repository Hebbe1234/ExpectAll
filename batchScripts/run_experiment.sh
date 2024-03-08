#!/bin/bash
EXPERIMENT=$1
RUN=$2
BASHFILE=${3-"./run_demands.sh"}


case $EXPERIMENT in
	0.1) #test super script
		outdir=super_script$RUN
		output=$(bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/simple.txt ../out/$outdir run_bdd.py baseline 5 1 15 1 $BASHFILE);
		echo $output; #not necessary, just to see jobs we await
		sbatch --dependency=afterany:$output ./make_single_graph.sh $EXPERIMENT $outdir;; 


	1.1)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/baseline_P2_v2$RUN run_bdd.py baseline_v2 2 2 10 5 $BASHFILE;
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/baseline_P3_v2$RUN run_bdd.py baseline_v2 3 2 10 5 $BASHFILE;;

	1.2)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/limited_P2_v2$RUN run_bdd.py limited_v2 2 2 10 5 $BASHFILE;
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/limited_P3_v2$RUN run_bdd.py limited_v2 3 2 10 5 $BASHFILE;;
	1.3)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/sequential_P2_v2$RUN run_bdd.py sequential_v2 2 2 10 5 $BASHFILE;
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/sequential_P3_v2$RUN run_bdd.py sequential_v2 3 2 10 5 $BASHFILE;;
	1.4)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/inc_par_P2_v2$RUN run_bdd.py inc-par_v2 2 2 10 5 $BASHFILE;
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/inc_par_P3_v2$RUN run_bdd.py inc-par_v2 3 2 10 5 $BASHFILE;;
	1.5)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/inc_par_limited_P2_v2$RUN run_bdd.py inc-par_limited_v2 2 2 10 5 $BASHFILE;
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/inc_par_limited_P3_v2$RUN run_bdd.py inc-par_limited_v2 3 2 10 5 $BASHFILE;;
	1.6)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/inc_par_seq_P2_v2$RUN run_bdd.py inc-par_sequential_v2 2 2 10 5 $BASHFILE;
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/inc_par_seq_P3_v2$RUN run_bdd.py inc-par_sequential_v2 3 2 10 5 $BASHFILE;;
	1.7)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/inc_par_lim_split_add_all_P2_v2$RUN run_bdd.py inc-par_limited_split_add_all_v2 2 2 10 5 $BASHFILE;
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/inc_par_lim_split_add_all_P3_v2$RUN run_bdd.py inc-par_limited_split_add_all_v2 3 2 10 5 $BASHFILE;;
	1.8)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/inc_parpar_limited_split_fancy_P2_v2$RUN run_bdd.py inc-par_limited_split_fancy_v2 2 2 10 5 $BASHFILE;
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/inc_parpar_limited_split_fancy_P3_v2$RUN run_bdd.py inc-par_limited_split_fancy_v2 3 2 10 5 $BASHFILE;;


























	3)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/add_all_split_graph_baseline$RUN run_bdd.py add_all_split_graph_baseline 8 1 15 1 $BASHFILE;;
	
	3.2)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/split_graph_lim_inc_par$RUN run_bdd.py split_graph_lim_inc_par 8 1 15 1 $BASHFILE;;
	3.3)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/split_graph_baseline$RUN run_bdd.py split_graph_baseline 8 1 15 1 $BASHFILE;;
	3.4)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/splitableNetworks/splitAble70.txt ../out/split_graph_fancy_lim_inc_par$RUN run_bdd.py split_graph_fancy_lim_inc_par 8 1 15 1 $BASHFILE;;





	4) # Both graph preprosseing
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_graph_preproccesing$RUN run_bdd.py graph_preproccesing 8 1 15 1 $BASHFILE;;
	
	4.1) # Both graph preprosseing
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_graph_preproccesing_all_graphs$RUN run_bdd.py graph_preproccesing 8 1 15 1 $BASHFILE;;

	5) # RSA baseline
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/rsa_bdd_baseline_run$RUN run_bdd.py rsa_baseline 0 3 5 5 $BASHFILE;;


	6.3)
		outdir=rsa_inc_par$RUN
		output=$(bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/rsa_inc_par_martin run_bdd.py rsa_inc_par 0 2 10 5 $BASHFILE);
		output+=":"
		output+=$(bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/rsa_lim_martin run_bdd.py rsa_lim 0 2 10 5 $BASHFILE);
		output+=":"
		output+=$(bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/rsa_inc_par_lim_martin run_bdd.py rsa_inc_par_lim 0 2 10 5 $BASHFILE);
		echo $output; #not necessary, just to see jobs we await
		sbatch --dependency=afterany:$output ./make_single_graph.sh $EXPERIMENT $outdir;; 
		
	7.1)
		outdir=rsa_inc_par$RUN
		output=$(bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/rsa_seq_martin run_bdd.py rsa_seq 0 2 10 5 $BASHFILE);
		output+=":"
		output+=$(bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/rsa_inc_par_seq_martin run_bdd.py rsa_inc_par_seq 0 2 10 5 $BASHFILE);
		echo $output; #not necessary, just to see jobs we await
		sbatch --dependency=afterany:$output ./make_single_graph.sh $EXPERIMENT $outdir;; 
		
	10) #run bdd, baseline
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_run$RUN run_bdd.py baseline 30 5 2 2 $BASHFILE;;
	10.2) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_demands_effect_run$RUN run_bdd.py baseline 15 15 1 1 $BASHFILE;;
	10.22) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_demands_effect_run2-2 run_bdd.py baseline 8 25 1 1 $BASHFILE;;
	10.23)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/simple.txt ../out/bdd_baseline2.32 run_bdd.py baseline 8 25 1 1 $BASHFILE;;
	10.3) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_wavelengths_effect_run$RUN run_bdd.py baseline 15 15 1 1 $BASHFILE;;
	10.32) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_wavelengths_effect_run3-2 run_bdd.py baseline 15 1 16 1 $BASHFILE;;	
	10.33) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_wavelengths_effect_run33 run_bdd.py baseline 15 16 1 1 $BASHFILE;;	

	11)	#bdd, wavelength constraint
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_run$RUN run_bdd.py wavelength_constraint 30 5 2 2 $BASHFILE;;
	11.2) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_run$RUN run_bdd.py wavelength_constraint 8 25 1 1 $BASHFILE;;
	
	11.22) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_16_demands run_bdd.py wavelength_constraint 8 1 16 1 $BASHFILE;;


	11.30)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 19 1 2 1 $BASHFILE;;
	11.31)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 19 1 4 1 $BASHFILE;;
	11.32)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 19 1 8 1 $BASHFILE;;	
	11.33)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 19 1 16 1 $BASHFILE;;
	11.34)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 19 1 32 1 $BASHFILE;;
	11.35)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 19 1 64 1 $BASHFILE;;
	11.36)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 19 1 128 1 $BASHFILE;;
	11.37)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 19 1 256 1 $BASHFILE;;


	11.40)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 15 1 2 1 $BASHFILE;;
	11.41)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 15 1 4 1 $BASHFILE;;
	11.42)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 15 1 8 1 $BASHFILE;;	
	11.43)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 15 1 16 1 $BASHFILE;;
	11.44)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 15 1 32 1 $BASHFILE;;
	11.45)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 15 1 64 1 $BASHFILE;;
	11.46)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 15 1 128 1 $BASHFILE;;
	11.47)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_powersof2$RUN run_bdd.py wavelength_constraint 15 1 256 1 $BASHFILE;;
	
	#baseline
	11.50)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/finish16.txt ../out/bdd_baseline_powersof2$RUN run_bdd.py baseline 15 1 2 1 $BASHFILE;;
	11.51)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/finish16.txt ../out/bdd_baseline_powersof2$RUN run_bdd.py baseline 15 1 4 1 $BASHFILE;;
	11.52)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/finish16.txt ../out/bdd_baseline_powersof2$RUN run_bdd.py baseline 15 1 8 1 $BASHFILE;;	
	11.53)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/finish16.txt ../out/bdd_baseline_powersof2$RUN run_bdd.py baseline 15 1 16 1 $BASHFILE;;
	11.54)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/finish16.txt ../out/bdd_baseline_powersof2$RUN run_bdd.py baseline 15 1 32 1 $BASHFILE;;
	11.55)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/finish16.txt ../out/bdd_baseline_powersof2$RUN run_bdd.py baseline 15 1 64 1 $BASHFILE;;
	11.56)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/finish16.txt ../out/bdd_baseline_powersof2$RUN run_bdd.py baseline 15 1 128 1 $BASHFILE;;
	11.57)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/finish16.txt ../out/bdd_baseline_powersof2$RUN run_bdd.py baseline 15 1 256 1 $BASHFILE;;
	12)	#bdd, increasing
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_run$RUN run_bdd.py increasing 30 5 2 2 $BASHFILE;;
	12.1)	#bdd, increasing parallel
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_parallel_run$RUN run_bdd.py increasing_parallel 8 1 15 1 $BASHFILE;;
	
	12.2)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_run2 run_bdd.py increasing 8 25 1 1 $BASHFILE;;
	
	12.3)	#bdd, increasing parallel sequential
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_parallel_sequential_run$RUN run_bdd.py increasing_parallel_sequential 8 1 15 1 $BASHFILE;;
	
	# encoded fixed paths rwa-inc-par-seq - demands - some 68
	12.4) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_parallel_sequential_encoded_fixed_paths_run_demands_some_68$RUN run_bdd.py encoded_3_fixed_paths_inc_par_seq 8 25 10 1 $BASHFILE;;
	
	# encoded fixed paths rwa-inc-par-seq-cliq - demands - some 68
	12.5) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_parallel_sequential_clique_encoded_fixed_paths_run_demands_some_68$RUN run_bdd.py encoded_3_fixed_paths_inc_par_seq_clique 8 25 10 1 $BASHFILE;;

	13) #wavelengths experiment 
		bash run_all.sh ../src ../src/topologies/topzoosynth_for_wavelengths/ ../src/topologies/wavelengths.txt ../out/bdd_wavelengths_static_demands_run$RUN run_bdd.py wavelengths_static_demands 10 10 1 1 $BASHFILE;;
	13.2) #wavelengths experiment
		bash run_all.sh ../src ../src/topologies/topzoosynth_for_wavelengths/ ../src/topologies/wavelengths2.txt ../out/bdd_wavelengths_static_demands_run$RUN run_bdd.py wavelengths_static_demands 10 20 1 1 $BASHFILE;;

	# encoded fixed paths rwa-inc-par-seq - wavelengths - some 68
	13.3) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_parallel_sequential_encoded_fixed_paths_run_wavelengths_some_68$RUN run_bdd.py encoded_3_fixed_paths_inc_par_seq 15 16 1 1 ./run_wavelengths.sh;;
	
	# encoded fixed paths rwa-inc-par-seq-cliq - wavelengths - some 68
	13.4) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_parallel_sequential_clique_encoded_fixed_paths_run_wavelengths_some_68$RUN run_bdd.py encoded_3_fixed_paths_inc_par_seq_clique 15 16 1 1 ./run_wavelengths.sh;;

	

	16) #only optimal -- caution
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_only_optimal run_bdd.py only_optimal 8 15 1 1 $BASHFILE;;
	
	16.1) #only optimal
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_only_optimal_all run_bdd.py only_optimal 8 1 15 1 $BASHFILE;;
			
	20) #mip, default
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/rsa_mip_default_run$RUN rsa_mip.py default 0 2 10 5 $BASHFILE;;
	
	# sequence
	31)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/sequence31_run$RUN run_bdd.py sequence 8 20 1 1 $BASHFILE;;

	31.2)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/sequence31_run2 run_bdd.py sequence 8 1 15 1 $BASHFILE;;
	41)  #edge encoding
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/simple.txt ../out/edge_encoding$RUN run_edge_encoding.py baseline 8 22 1 1 $BASHFILE;;
	42)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/edge_encoding_baseline run_edge_encoding.py baseline 8 1 15 1 $BASHFILE;;

	
	# default reordering
	51)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/10_over20.txt ../out/default_reodering_good_run$RUN run_bdd.py default_reordering 5 1 5 1 $BASHFILE;;
	51.1)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/10_over20.txt ../out/default_reodering_bad_run$RUN run_bdd.py default_reordering_bad 5 1 5 1 $BASHFILE;;
	# default reordering
	51.2)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/default_reodering_good_all_run$RUN run_bdd.py default_reordering 8 1 15 1 $BASHFILE;;
		# default reordering
	51.3)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/default_reodering_bad_all_run$RUN run_bdd.py default_reordering_bad 8 1 15 1 $BASHFILE;;
	
	# default reordering ee
	52)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/10_over20.txt ../out/default_reodering_ee_good_run$RUN run_bdd.py default_reordering_ee 5 1 5 1 $BASHFILE;;
	52.1)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/10_over20.txt ../out/default_reodering_ee_bad_run$RUN run_bdd.py default_reordering_ee_bad 5 1 5 1 $BASHFILE;;
	
	60) # baseline with naive fixed paths
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_naive_fixed_paths_all_graphs$RUN run_bdd.py naive_fixed_paths 15 8 1 1 ./run_wavelengths.sh;;
	
	60.1) # baseline with encoded paths
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_encoded_fixed_paths_all_graphs$RUN run_bdd.py encoded_fixed_paths 15 8 1 1 ./run_wavelengths.sh;;

	60.2) # baseline with encoded paths, sequential and parallel incremental approach
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_encoded_fixed_paths_inc_par_seq_all_graphs$RUN run_bdd.py encoded_paths_increasing_parallel_sequential 15 2 4 4 ./run_wavelengths.sh;;

	60.3) # baseline with "disjoint" encoded paths, sequential and parallel incremental approach
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_encoded_quote_unquote_disjoint_fixed_paths_inc_par_seq_all_graphs$RUN run_bdd.py encoded_disjoint_fixed_paths_inc_par_sec 15 4 1 1 ./run_wavelengths.sh;;
		
	60.4) # baseline with encoded paths, sequential and parallel incremental approach and clique pruning
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_encoded_fixed_paths_inc_par_seq_cliq_all_graphs$RUN run_bdd.py encoded_fixed_paths_inc_par_seq_cliq 15 2 4 4 ./run_wavelengths.sh;;

	# mip
	70)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/mip_source_aggregation_print$RUN mip.py source_aggregation_print 8 1 15 1 $BASHFILE;;
	


	99)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/wavelengths.txt ../out/print_demands run_bdd.py print_demands 30 5 2 2 $BASHFILE;;




	# Over christmas
	# mip
	100.1)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/mip_source_aggregation_$RUN mip.py source_aggregation 8 1 15 1 $BASHFILE;;
	# baseline
	100.2) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_baseline_run$RUN run_bdd.py baseline 8 1 15 1 $BASHFILE;;
	# rwa-inc
	100.3) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_increasing_run$RUN run_bdd.py increasing 8 1 15 1 $BASHFILE;;
	# rwa-seq
	100.4) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/sequence_run$RUN run_bdd.py sequence 8 1 15 1 $BASHFILE;;
	# rwa-lim
	100.5) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_wavelength_constraint_run$RUN run_bdd.py wavelength_constraint 8 1 15 1 $BASHFILE;;
	# rwa-inc-par
	100.6) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_increasing_parallel_run$RUN run_bdd.py increasing_parallel 8 1 15 1 $BASHFILE;;
	# rwa-conq-par
	100.7) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/dynamic_add_parallel$RUN run_dynamic.py parallel 8 1 15 1 $BASHFILE;;
	# rwa-inc-par-seq
	100.8) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_increasing_parallel_sequential_run$RUN run_bdd.py increasing_parallel_sequential 8 1 15 1 $BASHFILE;;
	# rwa-inc-par-seq
	100.81) # 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_increasing_parallel_sequential_reordering_run$RUN run_bdd.py increasing_parallel_sequential_reordering 8 1 15 1 $BASHFILE;;
	
	# rwa-conq-inc-par-lim 
	100.9) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_increasing_parallel_dynamic_limited_run_demands_all$RUN run_bdd.py increasing_parallel_dynamic_limited 8 1 15 1 $BASHFILE;;

	# baseline - demands - some 68 
	101.1) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_run_demands_some_68$RUN run_bdd.py baseline 8 25 1 1 $BASHFILE;;

	# baseline - demands - all
	101.2) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_baseline_run_demands_all$RUN run_bdd.py baseline 8 25 1 1 $BASHFILE;;

	# rwa-inc-par-seq - demands - some 68
	101.3) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_parallel_sequential_run_demands_some_68$RUN run_bdd.py increasing_parallel_sequential 8 25 1 1 $BASHFILE;;
	# rwa-inc-par-seq - demands - all
	101.4) # Has been run
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_increasing_parallel_sequential_run_demands_all$RUN run_bdd.py increasing_parallel_sequential 8 25 1 1 $BASHFILE;;

	102.1)  # rwa-inc-par-term
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_increasing_parallel_early_run$RUN run_bdd.py baseline 15 8 1 1 ./run_wavelengths.sh;;
	102.2) # rwa-inc-par-seq-term
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_increasing_parallel_sequential_early_run$RUN run_bdd.py sequence 15 8 1 1 ./run_wavelengths.sh;;
	102.3) #rwa-conq-inc-par-lim-term  ::: Remember to increase the timeout
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/all_topologies.txt ../out/bdd_increasing_parallel_dynamic_limited_early_run$RUN run_bdd.py dynamic_limited 15 8 1 1 ./run_wavelengths.sh;;

	103.1) # baseline wavelengths
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_run_wavelengths_some_68$RUN run_bdd.py baseline 15 16 1 1 ./run_wavelengths.sh;;

esac

