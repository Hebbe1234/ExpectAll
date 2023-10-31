
#!/bin/bash

FILENAME=$1

# takes demands as array
shift
demands=("$@")

cd ../../out/bdd_0
directory_name="res_$FILENAME"
mkdir "$directory_name"  


cd ../../batchScripts/bdd_0

for num in "${demands[@]}";
do
	output_file="../out/bdd_0/$directory_name/output${num}.txt"
	
	sbatch ./run_single.sh $FILENAME $output_file 30 $num
done
# Additional commands or post-processing can go here
exit
