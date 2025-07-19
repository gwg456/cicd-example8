#!/bin/bash

# Docker Hub域名IP地址更新脚本
# 用于解决中国大陆访问Docker Hub的网络问题

set -e

echo "🚀 开始更新Docker Hub域名IP地址..."

# 定义需要解析的Docker Hub域名
DOCKER_DOMAINS=(
    "registry-1.docker.io"
    "auth.docker.io"
    "production.cloudflare.docker.com"
    "index.docker.io"
    "registry.docker.io"
)

# 备用IP地址（如果DNS解析失败时使用）
declare -A FALLBACK_IPS=(
    ["registry-1.docker.io"]="52.4.71.198"
    ["auth.docker.io"]="54.85.56.253"
    ["production.cloudflare.docker.com"]="52.72.232.213"
    ["index.docker.io"]="52.1.38.175"
    ["registry.docker.io"]="52.4.71.198"
)

# 清理旧的Docker Hub配置
sudo sed -i '/# Docker Hub mirror configuration/,/# End Docker Hub configuration/d' /etc/hosts

# 添加新的配置开始标记
echo "# Docker Hub mirror configuration" | sudo tee -a /etc/hosts

for domain in "${DOCKER_DOMAINS[@]}"; do
    echo "🔍 解析域名: $domain"
    
    # 尝试使用多个DNS服务器解析
    ip=""
    for dns in "8.8.8.8" "1.1.1.1" "223.5.5.5"; do
        ip=$(nslookup $domain $dns 2>/dev/null | grep -A1 "Name:" | grep "Address:" | tail -1 | awk '{print $2}' | head -1)
        if [[ -n "$ip" && "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "✅ 通过DNS $dns 解析到IP: $ip"
            break
        fi
    done
    
    # 如果DNS解析失败，使用备用IP
    if [[ -z "$ip" || ! "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        ip="${FALLBACK_IPS[$domain]}"
        echo "⚠️  DNS解析失败，使用备用IP: $ip"
    fi
    
    # 添加到hosts文件
    if [[ -n "$ip" ]]; then
        echo "$ip    $domain" | sudo tee -a /etc/hosts
        echo "📝 已添加: $ip -> $domain"
    else
        echo "❌ 无法获取 $domain 的IP地址"
    fi
done

# 添加配置结束标记
echo "# End Docker Hub configuration" | sudo tee -a /etc/hosts

echo ""
echo "🎉 Docker Hub域名配置完成！"
echo ""
echo "📋 当前/etc/hosts中的Docker配置:"
grep -A 20 "# Docker Hub mirror configuration" /etc/hosts || echo "配置未找到"

echo ""
echo "🧪 测试连接性..."
for domain in "${DOCKER_DOMAINS[@]}"; do
    if ping -c 1 -W 2 $domain >/dev/null 2>&1; then
        echo "✅ $domain 连接正常"
    else
        echo "❌ $domain 连接失败"
    fi
done

echo ""
echo "💡 提示: 如果仍有问题，请考虑:"
echo "   1. 配置Docker镜像加速器"
echo "   2. 使用VPN或代理"
echo "   3. 手动更新IP地址"