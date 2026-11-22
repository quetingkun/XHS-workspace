#!/bin/bash
#===========================================
# 判断路径是文件还是目录
# 用法: ./check_path.sh <路径> [路径...]
#===========================================

set -euo pipefail

[[ $# -eq 0 ]] && {
    echo "用法: $0 <路径> [路径...]"
    echo "示例: $0 /etc/hosts /tmp /usr/bin"
    exit 1
}

check_path() {
    local p="$1"

    if [[ -L "$p" ]]; then
        local real
        real="$(readlink -f "$p" 2>/dev/null || echo "")"
        if [[ -f "$real" ]]; then
            echo "🔗 链接 → 文件 : $p  →  $real"
        elif [[ -d "$real" ]]; then
            echo "🔗 链接 → 目录 : $p  →  $real"
        else
            echo "🔗 链接 (目标无效) : $p"
        fi
    elif [[ -f "$p" ]]; then
        echo "📄 文件 : $p"
    elif [[ -d "$p" ]]; then
        echo "📁 目录 : $p"
    elif [[ -e "$p" ]]; then
        echo "❓ 其他类型 : $p (块设备/字符设备/socket 等)"
    else
        echo "❌ 不存在 : $p"
    fi
}

for path in "$@"; do
    check_path "$path"
done
