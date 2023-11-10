
#!/bin/bash

FILENAME=$1
OUT=$2
RUNFILE=$3
EXPERIMENT=$4
TOGRAPH=$5




# takes demands as array
demands=( 4 6 8 10 12 14)

cd ../out/$OUT
directory_name="res_$FILENAME"
mkdir "$directory_name"  

cd ../../batchScripts

for dem in "${demands[@]}";
do
        output_file="../out/$OUT/$directory_name/output${dem}.txt"

        sbatch ./run_single.sh $FILENAME $output_file 30 $dem $RUNFILE $EXPERIMENT "${TOGRAPH}" 
done

exit
