#! /bin/bash
set -euo pipefail
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin
IFSbak=$IFS

#grep精确检索并使用/d正则模式，uniq -c用于去重统计、sort -nr用于按数字排序
#grep -o -P '((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)' sample_access.log | sort | uniq -c | sort  -nr | head -n 10

#awk正则筛选
#grep "10.10.1.22 " sample_access.log  | awk -F" " '$9 ~ /2[0-9]+/ {print $9}'| wc

#grep+awk筛选状态码
#cat sample_access.log | grep -ioE "HTTP\/1\.[1|0]\"[[:blank:]][0-9]{3}" | awk -F" " '{print $2}' | sort | uniq -c | sort  -nr



#进行状态码占比检测
check_http_status()
{
	IFS=$'\n'
	local file=$1
	status=`grep -ioE "HTTP\/1\.[10]\"[[:blank:]][0-9]{3}" "$file"  | awk -F" " '{print $2}' | sort | uniq -c | sort  -nr`
	sums=`cat $file | wc -l`
	for var in $status
	do
		code=`echo $var | awk -F" " '{print($2)}'`
		num=`echo $var | awk -F" " '{print($1)}'`
		pj=$(echo "scale=2; $num / $sums*100" | bc)
		echo "$code占整体请求百分比为$pj%,数量为$num"
	done
	IFS=$IFSbak
}

check_http_ip()
{
	IFS=$'\n'
	local file=$1
	grep -o -P '((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)' "$file" | sort | uniq -c | sort  -nr | awk -F" " 'NR<11{print "请求IP为"$2",请求次数"$1}'
	IFS=$IFSbak
}


check_http_url()
{
        IFS=$'\n'
		local file=$1
        grep -oP " (\/\w*)+"  "$file" | sort | uniq  -c|sort -nr| awk -F" " 'NR<10{print $2"目录被访问了:"$1"次"}'
        IFS=$IFSbak
}


if	[ $# -eq 0 ]
then
	echo "请输入文件名"
	exit 1
else [ -f "$1" ]&&[ -s "$1" ]
	file=$1
	check_http_status "$file"
	check_http_ip "$file"
	check_http_url "$file"
fi
