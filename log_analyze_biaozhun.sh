#! /bin/bash
set -euo pipefail
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin

# ============================================================
# log_analyze.sh —— Nginx access.log 分析脚本（修正版）
# 用法：./log_analyze.sh <日志文件>
# 日志格式：IP - - [时间] "METHOD /path HTTP/1.1" 状态码 大小
# ============================================================

print_title() {
    echo "=================================================="
    echo "  $1"
    echo "=================================================="
}

check_http_status() {
    local file="$1"
    local matched total_lines
    matched=$(grep -ioE 'HTTP/1\.[10]"[[:blank:]]+[0-9]{3}' "$file" | wc -l)
    total_lines=$(wc -l < "$file")

    if [ "$matched" -eq 0 ]; then
        echo "未匹配到任何状态码，跳过占比统计。"
        return 0
    fi

    grep -ioE 'HTTP/1\.[10]"[[:blank:]]+[0-9]{3}' "$file" \
        | awk -v total="$matched" '
            {c[$2]++}
            END { for (k in c) printf "状态码 %s：占比 %.2f%%，数量 %d\n", k, c[k]/total*100, c[k] }' \
        | sort

    if [ "$total_lines" -gt "$matched" ]; then
        echo "（另有 $((total_lines - matched)) 行无法解析出状态码，未计入占比）"
    fi
}

check_http_ip() {
    local file="$1"
    grep -oE '((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])' "$file" \
        | sort | uniq -c | sort -nr \
        | awk 'NR<=10 {printf "  %-16s 请求 %d 次\n", $2, $1}'
}

check_http_url() {
    local file="$1"
    grep -oE ' (\/[A-Za-z0-9._-]*)+' "$file" \
        | sort | uniq -c | sort -nr \
        | awk 'NR<=10 {printf "  %-30s 被访问 %d 次\n", $2, $1}'
}

check_total() {
    local file="$1"
    echo "  总请求行数：$(wc -l < "$file")"
    echo "  独立 IP 数：$(grep -oE '^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])' "$file" | sort -u | wc -l)"
}

# ---------- 参数校验 ----------
if [ $# -eq 0 ]; then
    echo "用法: $0 <日志文件>" >&2
    exit 1
fi
if [ ! -f "$1" ]; then
    echo "错误: 文件不存在: $1" >&2
    exit 1
fi
if [ ! -s "$1" ]; then
    echo "错误: 文件为空: $1" >&2
    exit 1
fi
file="$1"

# ---------- 主流程 ----------
print_title "状态码占比";   check_http_status "$file"
print_title "TOP10 访问 IP"; check_http_ip "$file"
print_title "TOP10 请求路径"; check_http_url "$file"
print_title "总览";        check_total "$file"
