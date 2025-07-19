#!/bin/bash

# Docker 构建测试脚本
# 用于测试和比较不同 Dockerfile 的构建效果

set -e

echo "🐳 Docker 构建测试脚本"
echo "========================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函数：获取镜像大小
get_image_size() {
    local image_name=$1
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "$image_name" | awk '{print $2}'
}

# 函数：构建镜像并记录时间
build_image() {
    local dockerfile=$1
    local tag=$2
    local start_time=$(date +%s)
    
    print_info "构建镜像: $tag (使用 $dockerfile)"
    
    if docker build -f "$dockerfile" -t "$tag" . > /dev/null 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local size=$(get_image_size "$tag")
        print_success "构建成功: $tag (耗时: ${duration}s, 大小: $size)"
        echo "$tag,$duration,$size" >> build_results.csv
    else
        print_error "构建失败: $tag"
        return 1
    fi
}

# 函数：清理镜像
cleanup_images() {
    print_info "清理测试镜像..."
    docker rmi -f cicd-example:test cicd-example:multi-test cicd-example:prod-test 2>/dev/null || true
}

# 函数：运行容器测试
test_container() {
    local image_name=$1
    local container_name="test-${image_name//:/}"
    
    print_info "测试容器: $image_name"
    
    # 启动容器
    if docker run -d --name "$container_name" \
        -e PREFECT_API_URL=http://localhost:4200/api \
        -e DEPLOY_MODE=false \
        "$image_name" > /dev/null 2>&1; then
        
        # 等待容器启动
        sleep 5
        
        # 检查容器状态
        if docker ps | grep -q "$container_name"; then
            print_success "容器运行正常: $image_name"
            
            # 检查健康状态
            if docker inspect "$container_name" | grep -q '"Status": "healthy"'; then
                print_success "健康检查通过: $image_name"
            else
                print_warning "健康检查未通过: $image_name"
            fi
            
            # 停止并删除容器
            docker stop "$container_name" > /dev/null 2>&1
            docker rm "$container_name" > /dev/null 2>&1
        else
            print_error "容器启动失败: $image_name"
            docker logs "$container_name" 2>/dev/null || true
            docker rm -f "$container_name" 2>/dev/null || true
        fi
    else
        print_error "容器启动失败: $image_name"
    fi
}

# 主函数
main() {
    print_info "开始 Docker 构建测试..."
    
    # 创建结果文件
    echo "Image,Build Time (s),Size" > build_results.csv
    
    # 检查 Docker 是否运行
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker 未运行，请启动 Docker 服务"
        exit 1
    fi
    
    # 清理之前的测试镜像
    cleanup_images
    
    # 测试标准 Dockerfile
    if [ -f "Dockerfile" ]; then
        build_image "Dockerfile" "cicd-example:test"
        test_container "cicd-example:test"
    else
        print_error "Dockerfile 不存在"
    fi
    
    # 测试多阶段构建 Dockerfile
    if [ -f "Dockerfile.multi" ]; then
        build_image "Dockerfile.multi" "cicd-example:multi-test"
        test_container "cicd-example:multi-test"
    else
        print_warning "Dockerfile.multi 不存在，跳过测试"
    fi
    
    # 测试生产环境 Dockerfile
    if [ -f "Dockerfile.prod" ]; then
        build_image "Dockerfile.prod" "cicd-example:prod-test"
        test_container "cicd-example:prod-test"
    else
        print_warning "Dockerfile.prod 不存在，跳过测试"
    fi
    
    # 显示结果
    echo ""
    print_info "构建结果汇总:"
    echo "========================"
    if [ -f "build_results.csv" ]; then
        column -t -s ',' build_results.csv
    fi
    
    # 清理测试镜像
    cleanup_images
    
    print_success "测试完成！"
}

# 检查参数
case "${1:-}" in
    --help|-h)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h    显示帮助信息"
        echo "  --clean       清理所有测试镜像"
        echo ""
        echo "示例:"
        echo "  $0             运行完整测试"
        echo "  $0 --clean     清理测试镜像"
        ;;
    --clean)
        cleanup_images
        print_success "清理完成"
        ;;
    *)
        main
        ;;
esac