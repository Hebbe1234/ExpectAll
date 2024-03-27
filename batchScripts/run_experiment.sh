#!/bin/bash
EXPERIMENT=$1
RUN=$2
BASHFILE=${3-"./run_demands.sh"}

declare -a topologies=("kanto" "dt")



sub_commands=()
step_params="22 2 2"

p1s+=(0)
p2s+=(0)
p3s+=(0)
p4s+=(0)
p5s+=(0)

max_seed=5
case $EXPERIMENT in
	0.1)
		sub_commands=("baseline")
		step_params="1 1 1"
		;;
    411)
        sub_commands=("sub_spectrum")
        ;;
    412)
        sub_commands=("clique_and_limited")
        ;;
    6.3)
        sub_commands=("rsa_inc_par" "rsa_lim" "rsa_inc_par_lim")
        ;;
    7.1)
        sub_commands=("rsa_seq" "rsa_inc_par_seq")
        ;;

	# Super duper naive, one path, no path vars, size one for all demands, no modulation
    0.3)
        sub_commands=("single_path_limited_increasing")
        step_params="20 2 2"
        ;;
    0.4)
        sub_commands=("single_path_limited_increasing")
        step_params="20 30 2"
        ;;
	0.5)
		sub_commands=("single_path_limited_increasing")
		step_params="22 2 2"
		;;
	0.6)
		#1 path, inc, lim varying size demands, multiple seeds. 
		sub_commands=("single_path_limited_increasing_gravity_demands")
		step_params="20 2 2"
		;;

esac


read NUMBERDEMANDS STARTDEMAND INCREMENT <<< "$step_params"

for ((d=0; d<$NUMBERDEMANDS; d++));
do
	demands+=($(($STARTDEMAND+$d*$INCREMENT)))
done

for p1 in "${p1s[@]}"; do for p2 in "${p2s[@]}"; do for p3 in "${p3s[@]}"; do for p4 in "${p4s[@]}"; do for p5 in "${p5s[@]}"; do 
	for sub_command in "${sub_commands[@]}"; do
		for TOP in "${topologies[@]}"; do
			for ((SEED=1; SEED <= $max_seed; SEED++)); do
		
					outdir=../out/"$TOP"_"${sub_command}_$SEED_$RUN"
					mkdir $outdir
					echo $step_params

					DIR="../src/topologies/$TOP.txt"

					while read filename || [ -n "$filename" ]; do 
						directory_name="res_${filename}"
						mkdir $outdir/$directory_name
						for dem in "${demands[@]}";
						do	


							output_file="$outdir/$directory_name/output${dem}.txt"


							command=("../src/run_bdd.py")
							command+=("--experiment=$sub_command")
							command+=("--filename=../src/topologies/japanese_topologies/$filename")
							command+=("--demands=$dem")
							command+=("--par1=$p1")
							command+=("--par2=$p2")
							command+=("--par3=$p3")
							command+=("--par4=$p4")
							command+=("--par5=$p5")
							command+=("> $output_file")



							id=$(sbatch ./run_single.sh "$(printf "%s " "${command[@]}") > $output_file")
							job_ids+=($id) 
							job_ids+=(":") 
						done
					done < $DIR 
				
			done
		done
	done
done done done done done

# Remove the last colon
job_ids=("${job_ids[@]::${#job_ids[@]}-1}")

echo "${job_ids[@]}" # Not necessary, just to see jobs we await
sbatch --dependency=afterany:${job_ids[*]} ./make_single_graph.sh $EXPERIMENT $outdir





# OLD STUFF
# case $EXPERIMENT in
# 	0) #test (old) super script
# 		outdir=super_script$RUN
# 		output=$(bash run_all.sh ../src ../src/topologies/topzoo/ ../src/topologies/simple.txt ../out/$outdir run_bdd.py baseline 5 1 15 1 $BASHFILE );
# 		echo $output; #not necessary, just to see jobs we await
# 		sbatch --dependency=afterany:$output ./make_single_graph.sh $EXPERIMENT $outdir;; 
# esac

