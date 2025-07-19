#!/bin/bash

# 提取Docker Hub相关的hosts条目脚本
# 用于将宿主机的Docker Hub域名解析传递给Docker构建过程

set -e

echo "🔍 提取Docker Hub相关的hosts条目..."

# 输出文件
OUTPUT_FILE="docker-build-hosts.txt"
ADDHOST_FILE="docker-add-hosts.txt"

# 清理旧文件
rm -f "$OUTPUT_FILE" "$ADDHOST_FILE"

# Docker Hub相关域名模式
DOCKER_PATTERNS=(
    "docker\.io"
    "docker\.com" 
    "dockerhub"
    "registry-1\.docker\.io"
    "auth\.docker\.io"
    "production\.cloudflare\.docker\.com"
    "index\.docker\.io"
)

echo "# Docker Hub hosts extracted from /etc/hosts" > "$OUTPUT_FILE"
echo "# Generated on $(date)" >> "$OUTPUT_FILE"

found_entries=0

for pattern in "${DOCKER_PATTERNS[@]}"; do
    # 查找匹配的hosts条目
    matches=$(grep -E "$pattern" /etc/hosts | grep -v "^#" | grep -v "^$" || true)
    
    if [[ -n "$matches" ]]; then
        echo "$matches" >> "$OUTPUT_FILE"
        
        # 同时生成Docker --add-host格式
        while IFS= read -r line; do
            if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
                ip=$(echo "$line" | awk '{print $1}')
                hostname=$(echo "$line" | awk '{print $2}')
                if [[ -n "$ip" && -n "$hostname" ]]; then
                    echo "$hostname:$ip" >> "$ADDHOST_FILE"
                    found_entries=$((found_entries + 1))
                fi
            fi
        done <<< "$matches"
    fi
done

# 如果没有找到任何条目，使用默认的
if [[ $found_entries -eq 0 ]]; then
    echo "⚠️  未找到Docker Hub hosts条目，使用默认配置"
    
    # 默认的Docker Hub IP映射
    cat >> "$OUTPUT_FILE" << EOF
52.4.71.198     registry-1.docker.io
54.85.56.253    auth.docker.io
52.72.232.213   production.cloudflare.docker.com
52.1.38.175     index.docker.io
52.4.71.198     registry.docker.io
EOF

    # 默认的--add-host格式
    cat >> "$ADDHOST_FILE" << EOF
registry-1.docker.io:52.4.71.198
auth.docker.io:54.85.56.253
production.cloudflare.docker.com:52.72.232.213
index.docker.io:52.1.38.175
registry.docker.io:52.4.71.198
EOF
    found_entries=5
fi

echo "✅ 找到 $found_entries 个Docker Hub hosts条目"
echo ""
echo "📋 提取的hosts条目 ($OUTPUT_FILE):"
cat "$OUTPUT_FILE"
echo ""
echo "🐳 Docker --add-host格式 ($ADDHOST_FILE):"
cat "$ADDHOST_FILE"

# 生成GitHub Actions使用的格式
echo ""
echo "📝 GitHub Actions add-hosts格式:"
sed 's/:/: /' "$ADDHOST_FILE" | sed 's/^/            /'

echo ""
echo "🎉 Docker hosts提取完成！"