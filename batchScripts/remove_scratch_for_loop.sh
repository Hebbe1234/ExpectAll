a=(1 2 3 4 5 6 7 8 9)

for b in "${a[@]}"
do
    sbatch remove_scratch.sh
done