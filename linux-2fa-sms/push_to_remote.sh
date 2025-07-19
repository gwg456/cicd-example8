#!/bin/bash
# 推送到多个远程仓库的脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info "🚀 开始推送Linux SMS 2FA项目..."

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    print_error "当前目录不是Git仓库"
    exit 1
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    print_warning "检测到未提交的更改，请先提交"
    git status
    exit 1
fi

# 显示当前状态
print_info "📊 当前Git状态:"
echo "分支: $(git branch --show-current)"
echo "最近提交: $(git log --oneline -1)"
echo "标签: $(git tag | tail -1)"
echo ""

# 检查远程仓库配置
print_info "🔍 检查远程仓库配置..."
remotes=$(git remote)

if [ -z "$remotes" ]; then
    print_error "未配置任何远程仓库"
    print_info "请先配置远程仓库："
    echo "  git remote add origin https://github.com/YOUR_USERNAME/linux-sms-2fa.git"
    exit 1
fi

echo "已配置的远程仓库:"
git remote -v
echo ""

# 推送函数
push_to_remote() {
    local remote_name=$1
    local remote_url=$2
    
    print_info "📤 推送到 $remote_name ($remote_url)..."
    
    if git push "$remote_name" main 2>/dev/null; then
        print_success "$remote_name 主分支推送完成"
    else
        print_error "$remote_name 主分支推送失败"
        return 1
    fi
    
    if git push "$remote_name" --tags 2>/dev/null; then
        print_success "$remote_name 标签推送完成"
    else
        print_warning "$remote_name 标签推送失败"
    fi
    
    echo ""
}

# 遍历所有远程仓库并推送
success_count=0
total_count=0

for remote in $remotes; do
    total_count=$((total_count + 1))
    remote_url=$(git remote get-url "$remote")
    
    if push_to_remote "$remote" "$remote_url"; then
        success_count=$((success_count + 1))
    fi
done

# 显示推送结果
echo "📊 推送结果统计:"
echo "  总远程仓库: $total_count"
echo "  推送成功: $success_count"
echo "  推送失败: $((total_count - success_count))"
echo ""

if [ $success_count -eq $total_count ]; then
    print_success "🎉 所有远程仓库推送完成！"
elif [ $success_count -gt 0 ]; then
    print_warning "部分远程仓库推送完成"
else
    print_error "所有远程仓库推送失败"
    exit 1
fi

# 显示项目信息
print_info "📋 项目信息:"
echo "  项目名称: Linux SMS 2FA"
echo "  项目版本: $(git tag | tail -1)"
echo "  文件总数: $(find . -type f | grep -v '.git' | wc -l)"
echo "  代码行数: $(find . -name "*.py" -o -name "*.md" -o -name "*.sh" -o -name "*.conf" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')"
echo ""

print_info "🌐 仓库访问地址:"
for remote in $remotes; do
    remote_url=$(git remote get-url "$remote")
    # 转换为Web访问地址
    web_url=$(echo "$remote_url" | sed 's/\.git$//' | sed 's/git@github\.com:/https:\/\/github.com\//' | sed 's/git@gitlab\.com:/https:\/\/gitlab.com\//' | sed 's/git@gitee\.com:/https:\/\/gitee.com\//')
    echo "  $remote: $web_url"
done
echo ""

print_success "推送完成！您的Linux SMS 2FA项目现已在线可用 🎉"