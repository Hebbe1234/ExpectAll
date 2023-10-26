
#!/bin/bash

FILENAME=$1

# takes demands as array
shift
demands=("$@")

cd ../../out/bdd_1
directory_name="res_$FILENAME"
mkdir "$directory_name"  


cd ../../batchScripts/bdd_1

for num in "${demands[@]}";
do
	output_file="../out/bdd_1/$directory_name/output${num}.txt"
	bash ./run_single.sh $FILENAME $output_file $num $num
done
# Additional commands or post-processing can go here
exit