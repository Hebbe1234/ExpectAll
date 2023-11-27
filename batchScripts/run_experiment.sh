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
	
	10) #run bdd, baseline
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_run$RUN run_bdd.py baseline 30 5 2 2 $BASHFILE;;
	10.2) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_demands_effect_run$RUN run_bdd.py baseline 15 15 1 1 $BASHFILE;;
	10.3) 
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_baseline_wavenlengths_effect_run$RUN run_bdd.py baseline 15 15 1 1 $BASHFILE;;
	
	11)	#bdd, wavelength constraint
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_wavelength_constraint_run$RUN run_bdd.py wavelength_constraint 30 5 2 2 $BASHFILE;;
	12)	#bdd, wavelength constraint
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_increasing_run$RUN run_bdd.py increasing 30 5 2 2 $BASHFILE;;
	
	13) #wavelengths experiment
		bash run_all.sh ../src ../src/topologies/topzoosynth_for_wavelengths/ ../src/topologies/wavelengths.txt ../out/bdd_wavelengths_static_demands_run$RUN run_bdd.py wavelengths_static_demands 10 10 1 1 $BASHFILE;;
	13.2) #wavelengths experiment
		bash run_all.sh ../src ../src/topologies/topzoosynth_for_wavelengths/ ../src/topologies/wavelengths2.txt ../out/bdd_wavelengths_static_demands_run$RUN run_bdd.py wavelengths_static_demands 10 20 1 1 $BASHFILE;;

	14) # unary
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/bdd_unary_run$RUN run_bdd.py unary 10 10 1 1 $BASHFILE;;

	20) #mip, default
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/mip_default_run$RUN mip.py default 30 5 2 2 $BASHFILE;;
	21) #mip, source aggregation
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/mip_source_aggregation_run$RUN mip.py source_aggregation 30 5 2 2 $BASHFILE;;
	22) #mip, add_all
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/mip_add_all_run$RUN mip.py add_all 30 5 2 2 $BASHFILE;;
	23) #mip, add last
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/graphs_v2.txt ../out/mip_add_last_run$RUN mip.py add_last 30 5 2 2 $BASHFILE;;
	100)
		bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/wavelengths.txt ../out/print_demands run_bdd.py print_demands 30 5 2 2 $BASHFILE;;


esac

