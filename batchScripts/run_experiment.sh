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
path_types=("SHORTEST")

sbatch_timeout="1:00:00"
sbatch_mem="16G"

max_seed=5

out=EXPERIMENT_"${EXPERIMENT//./_}"_RUN_"${RUN}"
outdir=../out/$out
mkdir -p $outdir
plots=()

case $EXPERIMENT in
	0.1)
		experiments=("baseline")
		
		plots=(
			"fancy_scatter.py --data_dir=../$outdir/results --plot_cols=topology --plot_rows=num_paths"
			"fancy_scatter.py --data_dir=../$outdir/results --plot_cols=topology --plot_rows=num_paths --x_axis=size"
		)


		step_params="1 1 1"
		;;
    411)
        experiments=("sub_spectrum")
        ;;
    412)
        experiments=("clique_and_limited")
        ;;
    6.3)
        experiments=("rsa_inc_par" "rsa_lim" "rsa_inc_par_lim")
        ;;
    7.1)
        experiments=("rsa_seq" "rsa_inc_par_seq")
        ;;

	# Super duper naive, one path, no path vars, size one for all demands, no modulation
    0.3)
        experiments=("single_path_limited_increasing")
        step_params="1 1 1"
        ;;
    0.4)
        experiments=("single_path_limited_increasing")
        step_params="20 30 2"
        ;;
	0.5)
		experiments=("single_path_limited_increasing")
		step_params="22 2 2"
		;;
	0.6)
		#1 path, inc, lim varying size demands, multiple seeds. 
		experiments=("single_path_limited_increasing_gravity_demands")
		step_params="20 2 2"
		;;

esac


read NUMBERDEMANDS STARTDEMAND INCREMENT <<< "$step_params"

for ((d=0; d<$NUMBERDEMANDS; d++));
do
	demands+=($(($STARTDEMAND+$d*$INCREMENT)))
done

for p1 in "${p1s[@]}"; do for p2 in "${p2s[@]}"; do for p3 in "${p3s[@]}"; do for p4 in "${p4s[@]}"; do for p5 in "${p5s[@]}"; do 
	for path in "${paths[@]}"; do for path_type in "${path_types[@]}"; do
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
							command+=("--path_type=$path_type")

							command+=("--par1=$p1")
							command+=("--par2=$p2")
							command+=("--par3=$p3")
							command+=("--par4=$p4")
							command+=("--par5=$p5")

							# This must be the last argument in the command for run_single.sh to output to the correct place
							command+=("$outdir")

							id=$(sbatch --parsable --partition=dhabi --mem=$sbatch_mem--time=$sbatch_timeout ./run_single.sh "${command[@]}")
							job_ids+=($id) 
						done
					done
				done < $DIR 
					
			done
		done
	done done
done done done done done

# Remove the last colon
IFS=":"
echo "${job_ids[*]}" # Not necessary, just to see jobs we await

for plot in "${plots[@]}"; do
	echo "$plot"
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

