mkdir ../out/mytest2

for dir in ../out/bdd_0/*; do
	for file in $dir/*; do
		basedir=$(basename $dir)
		basefile=$(basename $file)
		solvetime=$(cat $file | grep "solve"  | awk -F'time:|\n' '{print $2}' | xargs)
		if [[ $solvetime != "" ]]
		then
		mkdir ../out/mytest2/$basedir
		echo "$solvetime, 0, True" > ../out/mytest2/$basedir/$basefile
		fi 

	done
done