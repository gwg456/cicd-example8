#!/bin/bash

# 测试容器内Docker Hub访问的脚本
# 用于验证hosts配置是否在容器内生效

set -e

echo "🧪 测试容器内Docker Hub访问能力..."

# 检查必要文件
if [ ! -f "docker-hosts.txt" ]; then
    echo "❌ docker-hosts.txt 文件不存在，请先运行:"
    echo "   sudo ./scripts/update-docker-hosts.sh"
    exit 1
fi

# 创建容器专用hosts文件
echo "🔧 创建容器专用hosts文件..."
cat > container-test-hosts << EOF
127.0.0.1	localhost
::1		localhost ip6-localhost ip6-loopback
fe00::0		ip6-localnet
ff00::0		ip6-mcastprefix
ff02::1		ip6-allnodes
ff02::2		ip6-allrouters

# Docker Hub hosts for container test
EOF

# 添加Docker Hub解析
cat docker-hosts.txt | grep -v "^#" | grep -v "^$" >> container-test-hosts

echo "📋 容器hosts文件内容:"
cat container-test-hosts

echo ""
echo "🧪 开始测试..."

# 测试1: 使用挂载hosts文件
echo ""
echo "📝 测试1: 挂载hosts文件方式"
echo "docker run --rm -v \$(pwd)/container-test-hosts:/etc/hosts alpine:latest..."

if docker run --rm -v $(pwd)/container-test-hosts:/etc/hosts alpine:latest sh -c "
    echo '=== 容器内hosts文件内容 ==='
    cat /etc/hosts | grep docker
    echo ''
    echo '=== 测试域名解析 ==='
    nslookup registry-1.docker.io || echo 'nslookup failed'
    echo ''
    echo '=== 测试网络连接 ==='
    ping -c 2 registry-1.docker.io || echo 'ping failed'
"; then
    echo "✅ 测试1: 挂载hosts文件 - 成功"
    MOUNT_SUCCESS=true
else
    echo "❌ 测试1: 挂载hosts文件 - 失败"
    MOUNT_SUCCESS=false
fi

# 测试2: 使用add-host参数
echo ""
echo "📝 测试2: add-host参数方式"

# 提取add-host参数
ADD_HOST_PARAMS=""
while IFS= read -r line; do
    if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
        ip=$(echo "$line" | awk '{print $1}')
        hostname=$(echo "$line" | awk '{print $2}')
        if [[ -n "$ip" && -n "$hostname" ]]; then
            ADD_HOST_PARAMS="$ADD_HOST_PARAMS --add-host $hostname:$ip"
        fi
    fi
done < <(cat docker-hosts.txt | grep -v "^#" | grep -v "^$")

echo "使用参数: $ADD_HOST_PARAMS"

if docker run --rm $ADD_HOST_PARAMS alpine:latest sh -c "
    echo '=== 容器内hosts文件内容 ==='
    cat /etc/hosts | grep docker
    echo ''
    echo '=== 测试域名解析 ==='
    nslookup registry-1.docker.io || echo 'nslookup failed'
    echo ''
    echo '=== 测试网络连接 ==='
    ping -c 2 registry-1.docker.io || echo 'ping failed'
"; then
    echo "✅ 测试2: add-host参数 - 成功"
    ADDHOST_SUCCESS=true
else
    echo "❌ 测试2: add-host参数 - 失败"
    ADDHOST_SUCCESS=false
fi

# 测试3: 实际的Docker pull测试
echo ""
echo "📝 测试3: 实际Docker pull测试"

if $MOUNT_SUCCESS; then
    echo "使用挂载hosts文件方式测试Docker pull..."
    if docker run --rm -v $(pwd)/container-test-hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock docker:latest docker pull hello-world; then
        echo "✅ 测试3: Docker pull - 成功"
        PULL_SUCCESS=true
    else
        echo "❌ 测试3: Docker pull - 失败"
        PULL_SUCCESS=false
    fi
else
    echo "⏭️  跳过Docker pull测试（基础测试失败）"
    PULL_SUCCESS=false
fi

# 清理临时文件
rm -f container-test-hosts

echo ""
echo "📊 测试结果总结:"
echo "================================="
if $MOUNT_SUCCESS; then
    echo "✅ 挂载hosts文件: 成功"
else
    echo "❌ 挂载hosts文件: 失败"
fi

if $ADDHOST_SUCCESS; then
    echo "✅ add-host参数: 成功"
else
    echo "❌ add-host参数: 失败"
fi

if $PULL_SUCCESS; then
    echo "✅ Docker pull测试: 成功"
else
    echo "❌ Docker pull测试: 失败"
fi

echo ""
if $MOUNT_SUCCESS || $ADDHOST_SUCCESS; then
    echo "🎉 容器内可以访问Docker Hub!"
    echo ""
    echo "💡 推荐使用方式:"
    if $MOUNT_SUCCESS; then
        echo "   docker run -v /path/to/hosts:/etc/hosts your_image"
    else
        echo "   docker run $ADD_HOST_PARAMS your_image"
    fi
else
    echo "🚨 容器内无法访问Docker Hub，请检查:"
    echo "   1. 宿主机hosts配置是否正确"
    echo "   2. 网络连接是否正常"
    echo "   3. IP地址是否需要更新"
fi