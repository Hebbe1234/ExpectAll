#!/bin/bash
EXPERIMENT=$1
RUN=$2
TOPOLOGYFILE=$3 #should be without .txt at the end

topologies=("kanto" "dt")
topology_dir=../src/topologies/japanese_topologies

if [ ! -z $3 ] ; then
	topologies=($TOPOLOGYFILE)
	topology_dir=../src/topologies/topzoo
	echo "custom topology file given. Only works for topzoo ;)"
fi

experiments=()
step_params="22 2 2"

p1s=(0)
p2s=(0)
p3s=(0)
p4s=(0)
p5s=(0)

paths=(1)

sbatch_timeout=60
sbatch_mem="50G"

min_seed=1
max_seed=5

#params for running gurobi. Set gurobi=true in gurobi experiments
gurobi=false
prev_job1=""
prev_job2=""
switcher=0


out=EXPERIMENT_"${EXPERIMENT//./_}"_RUN_"${RUN}"
outdir=../out/$out
mkdir -p $outdir
plots=()

case $EXPERIMENT in
	0.1)
		experiments=("baseline")
		max_seed=1
		step_params="30 2 2"
		paths=(50 1 2 3)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=experiment --aggregate=file --change_values_file num_paths"
		)
		;;
	

	0.11)
		experiments=("baseline" "baseline_demand_path")
		max_seed=3
		step_params="20 2 2"
		paths=(1 2 3)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --aggregate=file --line_values experiment --change_values_file seed"
		)
		;;
	
	0.12)
		experiments=("baseline" "baseline_dynamic_vars" "lim" "seq" "lim_seq" "dynamic_vars_seq" "dynamic_vars_lim" "dynamic_vars_lim_seq")
		max_seed=
		step_params="10 2 2"
		paths=(1 2 3)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=fake_row --plot_cols=num_paths --line_values experiment --aggregate=file --change_values_file topology"
		)
		;;
	
	0.13)
		experiments=("is_safe_lim_safe_big" "is_safe_lim_safe_small")
		max_seed=1
		step_params="5 5 1"
		paths=(1)
		sbatch_timeout=300
		;;

	0.14)
		experiments=("is_safe_gapfree_new")
		max_seed=1
		step_params="1 10 1"
		paths=(1)
		sbatch_timeout=300
		;;

  	0.2)
		sbatch_timeout=720
		experiments=("lim_inc" "seq_inc")
		max_seed=1
		step_params="30 2 2"
		paths=(50 1 2 3)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=experiment --aggregate=file --change_values_file num_paths"
		)
		;;

	0.3) 
		gurobi=true
		experiments=("mip_1")
		max_seed=1
		sbatch_mem="32G"
		step_params="20 5 5"
		paths=(50 1 2 3)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=experiment --aggregate=file --change_values_file num_paths experiment"
		)
		;;
	0.4) 
		gurobi=true
		experiments=("mip_all")
		max_seed=1
		sbatch_mem="32G"

		step_params="5 2 2"
		paths=(1 2)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=experiment --aggregate=file --change_values_file num_paths experiment"
		)
		;;
	0.5)
		experiments=("sub_spectrum")
		max_seed=1
		step_params="12 5 5"
		p1s=(2 3 4 5)
		paths=(1 2 3)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=par1 --aggregate=file --change_values_file num_paths experiment"
		)
		;;
	
	0.6)
		experiments=("baseline_dynamic_vars" "fixed_size_demands" "fixed_size_demands_dynamic_vars")
		max_seed=1
		step_params="10 2 2"
		p1s=(2 3 4 5 10)
		paths=(1 2 3)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=par1 --aggregate=file --change_values_file num_paths experiment"
		)
		;;
	
	0.7) 
		sbatch_timeout=240
		experiments=("fixed_channels")
		max_seed=1
		step_params="20 5 5"
		p1s=(1 2)
		p2s=(0 1)
		paths=(1 2 3 4 5)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=par2 --aggregate=file --change_values_file par1 num_paths experiment"
		)
		;;

	0.8) 
		sbatch_mem="10G"
		sbatch_timeout=30
		experiments=("fixed_channels_heuristics")
		max_seed=1
		step_params="20 5 5"
		p1s=(1 2)
		paths=(1 2 3 4 5)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=par1 --aggregate=file --change_values_file num_paths experiment"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=par1 --plot_cols=topology --aggregate=file --change_values_file num_paths experiment"
		)
		;;
	0.9)
		experiments=("baseline_lim_inc_usage" "fixed_channels_heuristics_usage")
		paths=(1 2 3)
		max_seed=3
		step_params="12 1 1"
		sbatch_timeout=240
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=experiment --plot_cols=topology --aggregate=file --y_axis usage --change_values_file num_paths"
		)
		;;
	1.0)
		experiments=("sub_spectrum_usage")
		paths=(1 2 3)
		max_seed=3
		p1s=(2 3 4 5)
		step_params="12 1 1"
		sbatch_timeout=240
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=par1 --aggregate=file --y_axis usage --change_values_file num_paths experiment"
		)
		;;
	
	1.1)
		experiments=("fixed_size_demands_usage")
		paths=(1 2 3)
		max_seed=3
		p1s=(2 3 4 5 10)
		step_params="12 1 1"
		sbatch_timeout=60
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=par1 --aggregate=file --y_axis usage --change_values_file num_paths experiment"
		)
		;;

	1.2)
		experiments=("sub_spectrum_usage")
		paths=(1 2 3)
		max_seed=3
		p1s=(2 3 4 5 10)
		step_params="20 5 5"
		sbatch_timeout=60
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=par1 --aggregate=file --y_axis usage --change_values_file num_paths experiment"
		)
		;;

	1.3)
		experiments=("fixed_channels_heuristics_usage")
		paths=(1 2 3)
		max_seed=3
		step_params="40 5 5"
		sbatch_timeout=60
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=par1 --aggregate=file --y_axis usage --change_values_file num_paths experiment"
		)
		;;

	3.1)
		gurobi=true
		experiments=("mip_edge_failover_n")
		paths=(1 2 3)
		max_seed=1
		p1s=(1 2 3)
		step_params="10 2 2"
		sbatch_timeout=60
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=par1 --aggregate=file --y_axis all_time --change_values_file num_paths experiment"
		)
		;;

	5.1)
		experiments=("safe_baseline" "safe_baseline_gap_free" "safe_baseline_upper_bound")
		min_seed=20001
		max_seed=20001

		paths=(1 2 3)
		step_params="15 1 1"
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
		)
		;;
	
	5.11)
		experiments=("safe_baseline_inc")
		min_seed=20001
		max_seed=20001
		sbatch_timeout=720
		paths=(1 2 3)
		step_params="15 1 1"
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
		)
		;;

	5.12)
		experiments=("safe_baseline_gapfree_upperbound")
		paths=(2)
		min_seed=20001
		max_seed=20001
		step_params="15 1 1"
		sbatch_timeout=60

		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
		)
		;;

	GAPFREE_INCREASING)
		experiments=("safe_baseline_gapfree_increasing")
		min_seed=20001
		max_seed=20001
		sbatch_timeout=720
		paths=(2)
		step_params="15 1 1"

		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
		)
		;;

	GAPFREE)
		experiments=("safe_baseline_gap_free")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="15 1 1"
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
		)
		;;

	SUPER_SAFE_UPPER_BOUND)
		experiments=("safe_baseline_super_safe_upperbound" "safe_gapfree_super_safe_upperbound")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="15 1 1"

		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file seed"
		)
		;;
	6.1)
		experiments=("unsafe_limited" "unsafe_safe_limited" "unsafe_gap_free_limited" "unsafe_gap_free_safe_limited")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="30 1 1"
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file seed"
		)
		;;
	
	6.2) 
		experiments=("unsafe_rounded_channels")
		min_seed=20001
		paths=(2)
		step_params="30 1 1"
		p1s=(2 5 10)
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file seed"
		)
		;;

	6.21) 
		experiments=("unsafe_sub_spectrum")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="60 1 1"
		p1s=(2 5 10)
		sbatch_timeout=720
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis solve_time --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis usage --change_values_file seed"
		)
		;;

	6.22)
		experiments=("unsafe_clique" "unsafe_clique_limit" "unsafe_heuristics")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="30 1 1"
		
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file seed"
		)
		;;
	6.3)
		gurobi=true
		experiments=("mip_1")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="60 1 1"
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file seed"
		)
		;;

	MIP_EX_AND_PATH)
		gurobi=true
		experiments=("mip_exhaustive" "mip_path_optimal")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="30 1 1"
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file seed"
		)
		;;
	
	MIP_SAFE)
		gurobi=true
		experiments=("mip_safe")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="30 1 1"
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
		)
		;;

	MONDAY_MEETING_MOST_EXPS)
		experiments=("baseline" "gap_free" "super_safe_upperbound" "heuristic_upper_bound" "limited" "safe_limited" "clique" "clique_internal_limit" "gap_free_super_safe_upperbound" "gap_free_limited" "gap_free_safe_limited")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="15 1 1"
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file experiment seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file experiment seed"
		
		)
		;;

	MONDAY_MEETING_INCREASING)
		experiments=("increasing")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="15 1 1"
		sbatch_timeout=720
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file experiment seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file experiment seed"
		)
		;;

	MONDAY_MEETING_SUB_SPECTRUM)
		experiments=("sub_spectrum")
		min_seed=20001
		max_seed=20001
		paths=(2)
		p1s=(2 5 10)
		step_params="60 1 1"
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis solve_time --change_values_file seed "
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis usage --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis solve_time --change_values_file experiment seed "
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis usage --change_values_file experiment seed"
		
		)
		;;

	MONDAY_MEETING_HEURISTIC)
		experiments=("fast_heuristic")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="60 1 1"
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file experiment seed"
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis usage --change_values_file experiment seed"
		
		)
		;;


	FAILOVER)
		experiments=("failover_dynamic_query" "failover_failover_query")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="15 1 1"
		p1s=(1 2 3)
		p2s=(100)
		plots=(			
		"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis solve_time --change_values_file seed topology"
		)
	;;


	FAILOVER_MIP)
		experiments=(failover_mip_n_query)
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="15 1 1"
		p1s=(3)
		p2s=(100)
		sbatch_timeout=10800
	;;


	
	FAILURE_N_MIP)
		gurobi=true
		experiments=("mip_edge_failover_n")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="15 1 1"
		p1s=(1 2 3)
		plots=(			
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis solve_time --change_values_file seed topology"
		)
		;;
	
	FAILURE_N_HEURISTIC)
		experiments=("heuristic_edge_failover_n")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="15 1 1"
		p1s=(1 2 3)
		plots=(			
			"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis solve_time --change_values_file seed topology"
		)
		;;
	
esac


read NUMBERDEMANDS STARTDEMAND INCREMENT <<< "$step_params"

for ((d=0; d<$NUMBERDEMANDS; d++));
do
	demands+=($(($STARTDEMAND+$d*$INCREMENT)))
done

for p1 in "${p1s[@]}"; do for p2 in "${p2s[@]}"; do for p3 in "${p3s[@]}"; do for p4 in "${p4s[@]}"; do for p5 in "${p5s[@]}"; do 
	for path in "${paths[@]}"; do 
		for experiment in "${experiments[@]}"; do
			for TOP in "${topologies[@]}"; do
				DIR="../src/topologies/$TOP.txt"
				while read filename || [ -n "$filename" ]; do 
					for dem in "${demands[@]}";
					do	
						for ((SEED=$min_seed; SEED <= $max_seed; SEED++)); do
							command=("../src/run_bdd.py")
							command+=("--experiment=$experiment")
							command+=("--filename=$topology_dir/$filename")
							command+=("--seed=$SEED")
							command+=("--demands=$dem")

							command+=("--num_paths=$path")

							command+=("--par1=$p1")
							command+=("--par2=$p2")
							command+=("--par3=$p3")
							command+=("--par4=$p4")
							command+=("--par5=$p5")

							# This must be the last argument in the command for run_single.sh to output to the correct place
							command+=("$outdir")
							IFS=":"

							if [ "$gurobi" = true ] ; then
								#each job awaits for every second job
								if [ "$switcher" = 0 ] ; then
									if [ "$prev_job1" = "" ] ; then
										prev_job1=$(sbatch --parsable --partition=dhabi --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
									else 
										prev_job1=$(sbatch --parsable --dependency=afterany:$prev_job1 --partition=dhabi --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
									fi
									
									job_ids+=($prev_job1)
									switcher=1
								elif [ "$switcher" = 1 ] ; then
									if [ "$prev_job2" = "" ] ; then
										prev_job2=$(sbatch --parsable --partition=dhabi --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
									else 
										prev_job2=$(sbatch --parsable --dependency=afterany:$prev_job2 --partition=dhabi --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
									fi
									job_ids+=($prev_job2)
									switcher=0
								fi

							else #run as normal, not gurobi
								id=$(sbatch --parsable --partition=dhabi --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
								job_ids+=($id) 
							fi
						done
					done
				done < $DIR 
					
			done
		done
	done 
done done done done done

# Remove the last colon
IFS=":"
echo "${job_ids[*]}" # Not necessary, just to see jobs we await

for plot in "${plots[@]}"; do
	sbatch --dependency=afterany:"${job_ids[*]}" ./make_plot.sh $plot $outdir
done






# OLD STUFF
# case $EXPERIMENT in
# 	0) #test (old) super script
# 		outdir=super_script$RUN
# 		output=$(bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/simple.txt ../out/$outdir run_bdd.py baseline 5 1 15 1 $BASHFILE );
# 		echo $output; #not necessary, just to see jobs we await
# 		sbatch --dependency=afterany:$output ./make_single_graph.sh $EXPERIMENT $outdir;; 
# esac
