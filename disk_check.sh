#! /bin/bash

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin

if [[ "$1" =~ ^[0-9]+$  ]] 
then
	w=$1
else
	echo "请输入0~100的数字"
fi



df -P | awk -v score_threshold="$w" 'NR>1&&$3/($3+$4)*100>score_threshold {print "分区"$6":占用率过高总计占用:"$5}' > check.log


