
#!/bin/bash
#SBATCH --time=0:05:00
#SBATCH --mail-user=mpha19@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=naples
#SBATCH --mem=15000
FILENAME=$1

shift

demands=("$@")

# Change to the directory where your Python script is located
# Create and activate a virtual environment
# Run your Python script

directory_name="res_$FILENAME"

if [ -d "$directory_name" ]; then
    	echo "The directory '$directory_name' already exists."
	else  
	  # Create the directory   
		mkdir "$directory_name"   
		echo "Directory '$directory_name' reated successfully."
fi

for num in "${demands[@]}";
do
	output_file="$directory_name/output${num}.txt"
	#python mip.py --filename=$FILENAME --wavelengths=$num --demands=$num > $output_file
	bash ./run_single_mip.sh $FILENAME $num $num
done
# Additional commands or post-processing can go here
exit