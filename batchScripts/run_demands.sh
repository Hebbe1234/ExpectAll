
#!/bin/bash

FILENAME=$1
OUT=$2
EXPERIMENT=$3

# takes demands as array
shift
shift
shift
demands=("$@")

cd ../out/$OUT
directory_name="res_$FILENAME"
mkdir "$directory_name"  

cd ../../batchScripts

for num in "${demands[@]}";
do
        output_file="../out/$OUT/$directory_name/output${num}.txt"

        sbatch ./run_single.sh $FILENAME $output_file 30 $num $EXPERIMENT
done

exit
