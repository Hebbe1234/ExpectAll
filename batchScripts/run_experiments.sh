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
max_array=0

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

    GAP_FREE)
        # Used for Figure 4 and 5
		experiments=("gap_free_safe_limited_super_safe" "gap_free_concrete_safe_limited_super_safe")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="11 1 1"
		plots=(			
		"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis solve_time --change_values_file seed topology"
		"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment --aggregate=file --y_axis gap_free_time --change_values_file seed topology"
		)
		sbatch_timeout=1440 #24h
		sbatch_mem="30G"
	;;



	FAILOVER_MIP)
        # Used for Figure 3, Table 1, Figure 4 and Figure 6
		gurobi=true
		experiments=(failover_mip_n_query)
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="10 1 1"
		p1s=(5)
		p2s=(100)
		sbatch_timeout=180 # 3h
		sbatch_mem="30G"

	;;


	FAILOVER)
        # Used for Figure 4 and 5
		experiments=("failover_dynamic_query" "failover_failover_query")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="9 1 1"
		p1s=(5)
		p2s=(1000)
		plots=(			
		"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis solve_time --change_values_file seed topology"
		)
		sbatch_timeout=1440 #24h
		sbatch_mem="50G"

	;;

	FAILOVER_BUILD_QUERY)
        # Used for Figure 6
		experiments=("failover_dynamic_build_query" "failover_failover_build_query")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="9 1 1"
		p5s=(0 1 2 3 4 5)
		plots=(			
		"fancy_scatter.py --data_dir=../$outdir/results --save_dir=$out --plot_rows=topology --plot_cols=num_paths --line_values experiment par1 --aggregate=file --y_axis solve_time --change_values_file seed topology"
		)
		sbatch_timeout=1440 #24h
		sbatch_mem="30G"

	;;

	
	K_LINK_RESIL)
        # Used to evaluate if limited i k link resilient (Section 4.2)
		experiments=("evaluate_k_link_resillience")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="3 4 1"
		p5s=(3 4 5)
		;;
	
	CLIQUE_RESIL)
        # Used for Figure 7c
		experiments=("clique_resilience")
		min_seed=20001
		max_seed=20001
		paths=(2)
		step_params="1 6 1"
		p5s=(3)
		;;


	TOPOLOGY_ZOO_BEST)
        max_array=30
        step_params="1 1 1" #max array takes care of demands, just need to put 1 here
        experiments=("topozoo_best")
        min_seed=20001
        max_seed=20001
        paths=(2)
        sbatch_timeout=60
        sbatch_mem=20G
        p5s=("no population")
 
        ;;
 
	TOPOLOGY_ZOO_CLIQUE)
        max_array=30
        step_params="1 1 1" #max array takes care of demands, just need to put 1 here
        experiments=("topozoo_best_clique")
        min_seed=20001
        max_seed=20001
        paths=(2)
        sbatch_timeout=60
        sbatch_mem=20G
        p5s=("no population")
 
        ;;

	TOPOLOGY_ZOO_SUB_SPECTRUM)
        max_array=150
        step_params="1 1 1" #max array takes care of demands, just need to put 1 here
        experiments=("topozoo_best_subspectrum")
        min_seed=20001
        max_seed=20001
        paths=(2)
        sbatch_timeout=60
        sbatch_mem=20G
        p5s=("no population")
 
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
										prev_job1=$(sbatch --parsable --partition=naples --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
									else 
										prev_job1=$(sbatch --parsable --dependency=afterany:$prev_job1 --partition=naples --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
									fi
									
									job_ids+=($prev_job1)
									switcher=1
								elif [ "$switcher" = 1 ] ; then
									if [ "$prev_job2" = "" ] ; then
										prev_job2=$(sbatch --parsable --partition=naples --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
									else 
										prev_job2=$(sbatch --parsable --dependency=afterany:$prev_job2 --partition=naples --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
									fi
									job_ids+=($prev_job2)
									switcher=0
								fi
							elif [ $max_array -gt 0 ] ; then
                                sbatch --array=5-$max_array:5 --partition=naples --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}"
							else #run as normal, not gurobi
								id=$(sbatch --parsable --partition=naples --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
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





