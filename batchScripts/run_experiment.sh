#!/bin/bash
EXPERIMENT=$1
RUN=$2

topologies=("kanto" "dt")
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

		step_params="30 2 2"
		paths=(50 1 2 3)
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
		experiments=("fixed_size_demands")
		max_seed=1
		step_params="8 5 5"
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
						for ((SEED=1; SEED <= $max_seed; SEED++)); do
							command=("../src/run_bdd.py")
							command+=("--experiment=$experiment")
							command+=("--filename=../src/topologies/japanese_topologies/$filename")
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

							if [ "$gurobi" = true ] ; then
								#each job awaits for every second job
								if [ "$switcher" = 0 ] ; then
									prev_job1=$(sbatch --parsable --dependency=afterany:"$prev_job1" --partition=dhabi --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
									job_ids+=($prev_job1)
									switcher=1
								elif [ "$switcher" = 1 ] ; then
									prev_job2=$(sbatch --parsable --dependency=afterany:"$prev_job2" --partition=dhabi --mem=$sbatch_mem --time=$sbatch_timeout ./run_single.sh "${command[@]}")
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
