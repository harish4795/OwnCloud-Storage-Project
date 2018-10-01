#!/bin/bash
username=$1
while inotifywait -r -e close_write,delete ~/OwnCloud/ >| ~/OwnCloud/log.txt; do
	cat ~/OwnCloud/log.txt > ~/OwnCloud/log2.txt
	while read p; do
		if [[ $p == *CLOSE_WRITE* ]];
		then
			if [[ $p == *.swp* || $p == *.swx* ]];then
				continue
			else
				wordstring=($p)
				IFS=' ' read -ra wordstring <<<"$p"
				for words in "${wordstring[@]}"
				do
					echo $words
				done
				filePath=${wordstring[0]}
				filename=${wordstring[2]}
				command=$(echo 'scp '"$filePath""$filename" 'root@10.10.10.3:~/'"$username"'/'"$filename")
				echo $command
				${command};
			fi
		fi
		if [[ $p == *DELETE* ]];
		then
			#echo "do nothing"
	
        		if [[ $p == *.swp* || $p == *.swx* ]];then
                        	continue
			
			else
				wordstring=($p)
				IFS=' ' read -ra wordstring <<<"$p"
				for words in "${wordstring[@]}"
				do 
					echo $words
				done
				filename=${wordstring[2]}
				eval "$(echo 'ssh root@10.10.10.3 "echo ""$username $filename" " >> ~/Deletelog/""$username""_delete.txt"')"
			fi 
		fi
	done <~/OwnCloud/log2.txt
done
