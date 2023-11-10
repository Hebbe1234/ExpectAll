#!/bin/bash
EXPERIMENT=$1
RUN=$2
BASHFILE=${3-"./run_demands.sh"}


case $EXPERIMENT in
	0) #run dynamic, add_all
		bash run_all.sh ../src ../src/topologies/graphs_v2.txt ../out/dynamic_add_all_run$RUN run_dynamic.py add_all 30 5 2 2 $BASHFILE;;
	1) #run dynamic, add last
		bash run_all.sh ../src ../src/topologies/graphs_v2.txt ../out/dynamic_add_last_run$RUN run_dynamic.py add_last 30 5 2 2 $BASHFILE;;
	10) #run bdd, baseline
		bash run_all.sh ../src ../src/topologies/graphs_v2.txt ../out/bdd_baseline_run$RUN run_bdd.py baseline 30 5 2 2 $BASHFILE;;
	11)	#bdd, wavelength constraint
		bash run_all.sh ../src ../src/topologies/graphs_v2.txt ../out/bdd_increasig_run$RUN run_bdd.py wavelength_constraint 30 5 2 2 $BASHFILE;;
	20) #mip, default
		bash run_all.sh ../src ../src/topologies/graphs_v2.txt ../out/mip_default_run$RUN mip.py default 30 5 2 2 $BASHFILE;;
	21) #mip, source aggregation
		bash run_all.sh ../src ../src/topologies/graphs_v2.txt ../out/mip_source_aggregation_run$RUN mip.py source_aggregation 30 5 2 2 $BASHFILE;;
	22) #mip, add_all
		bash run_all.sh ../src ../src/topologies/graphs_v2.txt ../out/mip_add_all_run$RUN mip.py add_all 30 5 2 2 $BASHFILE;;
	23) #mip, add last
		bash run_all.sh ../src ../src/topologies/graphs_v2.txt ../out/mip_add_last_run$RUN mip.py add_last 30 5 2 2 $BASHFILE;;
	100)
		bash run_all.sh ../src ../src/topologies/wavelengths.txt ../out/print_demands run_bdd.py print_demands 30 5 2 2 $BASHFILE;;


esac
