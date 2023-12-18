#!/bin/bash
EXPERIMENT=$1
RUN=$2
BASHFILE=${3-"./run_demands.sh"}


case $EXPERIMENT in
	0) #run dynamic, add_all
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/dynamic_add_all_run$RUN run_dynamic.py add_all 30 5 2 2 $BASHFILE;;
	1) #run dynamic, add last
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/dynamic_add_last_run$RUN run_dynamic.py add_last 30 5 2 2 $BASHFILE;;
	1.2)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/dynamic_add_last_1.2_run$RUN run_dynamic.py add_last 15 14 2 1 $BASHFILE;;
	1.3)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/dynamic_add_last_1.3_run$RUN run_dynamic.py add_last 8 20 2 1 $BASHFILE;;
	
	2) 	
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/dynamic_add_last_wavelength_constraint$RUN run_dynamic.py add_last_wavelength_constraint 8 25 2 1 $BASHFILE;;

	2.1) 	
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/dynamic_add_last_wavelength_constraint_n$RUN run_dynamic.py add_last_wavelength_constraint_n 16 15 1 1 $BASHFILE;;


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
	12)	#bdd, increasing
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_run$RUN run_bdd.py increasing 30 5 2 2 $BASHFILE;;
	12.2)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_run2 run_bdd.py increasing 8 25 1 1 $BASHFILE;;
	
	
	13) #wavelengths experiment
		bash run_all.sh ../src ../src/topologies/topzoosynth_for_wavelengths/ ../src/topologies/wavelengths.txt ../out/bdd_wavelengths_static_demands_run$RUN run_bdd.py wavelengths_static_demands 10 10 1 1 $BASHFILE;;
	13.2) #wavelengths experiment
		bash run_all.sh ../src ../src/topologies/topzoosynth_for_wavelengths/ ../src/topologies/wavelengths2.txt ../out/bdd_wavelengths_static_demands_run$RUN run_bdd.py wavelengths_static_demands 10 20 1 1 $BASHFILE;;

	14) # unary
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_unary_run$RUN run_bdd.py unary 10 10 1 1 $BASHFILE;;

	15) #best
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_best$RUN run_bdd.py best 64 30 1 1 $BASHFILE;;

	16) #only optimal
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_only_optimal run_bdd.py only_optimal 8 9 10 1 $BASHFILE;;
		
	20) #mip, default
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/mip_default_run$RUN mip.py default 30 5 2 2 $BASHFILE;;
	21) #mip, source aggregation
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/mip_source_aggregation_run$RUN mip.py source_aggregation 8 25 1 1 $BASHFILE;;
	22) #mip, add_all
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/mip_add_all_run$RUN mip.py add_all 30 5 2 2 $BASHFILE;;
	23) #mip, add last
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/mip_add_last_run$RUN mip.py add_last 30 5 2 2 $BASHFILE;;

	24) #mip, source aggregation
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/mip_source_aggregation_limit_run$RUN mip.py source_aggregation 64 10 50 50 $BASHFILE;;
	
	# sequence
	31)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/sequence31_run$RUN run_bdd.py sequence 8 20 1 1 $BASHFILE;;
	
	41)  #edge encoding
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/simple.txt ../out/edge_encoding$RUN run_edge_encoding.py baseline 8 22 1 1 $BASHFILE;;
	
	# default reordering
	51)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/10_over20.txt ../out/default_reodering_good_run$RUN run_bdd.py default_reordering 5 1 5 1 $BASHFILE;;
	51.1)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/10_over20.txt ../out/default_reodering_bad_run$RUN run_bdd.py default_reordering_bad 5 1 5 1 $BASHFILE;;
	
	100)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/wavelengths.txt ../out/print_demands run_bdd.py print_demands 30 5 2 2 $BASHFILE;;


esac

