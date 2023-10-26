
#!/bin/bash


#TODO: bedøm hvor det ovenstående skal stå ift. at lave jobs

FILENAME=$1

# takes demands as array
shift
demands=("$@")

cd ../out/mip
directory_name="res_$FILENAME"
mkdir "$directory_name"  


cd ../../batchScripts

for num in "${demands[@]}";
do
	output_file="../out/mip/$directory_name/output${num}.txt"
	bash ./run_single_mip.sh $FILENAME $output_file $num $num
done
# Additional commands or post-processing can go here
exit