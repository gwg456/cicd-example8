#!/bin/bash
# 安全推送脚本 - Linux SMS 2FA项目

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

print_header() {
    echo -e "${CYAN}🔐 Linux SMS 2FA 安全推送脚本${NC}"
    echo -e "${CYAN}================================${NC}"
    echo ""
}

print_header

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    print_error "当前目录不是Git仓库"
    exit 1
fi

# 检查当前认证状态
print_info "📋 检查Git配置..."
echo "用户名: $(git config user.name 2>/dev/null || echo '未设置')"
echo "邮箱: $(git config user.email 2>/dev/null || echo '未设置')"
echo "远程仓库: $(git remote get-url origin 2>/dev/null || echo '未设置')"
echo ""

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    print_warning "检测到未提交的更改"
    git status --short
    echo ""
    read -p "是否继续推送? (y/N): " continue_push
    if [[ ! $continue_push =~ ^[Yy]$ ]]; then
        print_info "推送已取消"
        exit 0
    fi
fi

# 显示项目信息
print_info "📊 项目状态:"
echo "分支: $(git branch --show-current)"
echo "最近提交: $(git log --oneline -1)"
echo "标签: $(git tag | tail -1 || echo '无')"
echo "文件数: $(find . -type f | grep -v '.git' | wc -l)"
echo ""

# 选择认证方式
echo "请选择认证方式:"
echo "1) 个人访问令牌 (HTTPS) - 推荐"
echo "2) SSH密钥"
echo "3) GitHub CLI"
echo "4) 仅显示推送命令"
echo ""
read -p "请输入选择 (1-4): " auth_method

case $auth_method in
    1)
        print_info "使用个人访问令牌推送"
        echo ""
        echo "请按照以下步骤获取Personal Access Token:"
        echo "1. 访问 https://github.com/settings/tokens"
        echo "2. 点击 'Generate new token (classic)'"
        echo "3. 选择 'repo' 权限"
        echo "4. 复制生成的token"
        echo ""
        read -p "请输入您的GitHub Personal Access Token: " -s token
        echo ""
        
        if [ -z "$token" ]; then
            print_error "Token不能为空"
            exit 1
        fi
        
        # 设置包含token的远程URL
        git remote set-url origin https://$token@github.com/samples28/ggggg.git
        print_success "已配置Personal Access Token"
        ;;
        
    2)
        print_info "使用SSH密钥推送"
        git remote set-url origin git@github.com:samples28/ggggg.git
        
        # 测试SSH连接
        print_info "测试SSH连接..."
        if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
            print_success "SSH连接正常"
        else
            print_warning "SSH连接可能有问题，但仍会尝试推送"
        fi
        ;;
        
    3)
        print_info "使用GitHub CLI推送"
        
        # 检查gh是否安装
        if ! command -v gh &> /dev/null; then
            print_error "GitHub CLI (gh) 未安装"
            print_info "请先安装: https://cli.github.com/"
            exit 1
        fi
        
        # 检查认证状态
        if ! gh auth status &> /dev/null; then
            print_info "需要先登录GitHub CLI"
            gh auth login
        fi
        ;;
        
    4)
        print_info "推送命令:"
        echo ""
        echo "🔗 方案1: 使用Personal Access Token"
        echo "git remote set-url origin https://YOUR_TOKEN@github.com/samples28/ggggg.git"
        echo "git push -u origin main"
        echo "git push origin --tags"
        echo ""
        echo "🔗 方案2: 使用SSH"
        echo "git remote set-url origin git@github.com:samples28/ggggg.git" 
        echo "git push -u origin main"
        echo "git push origin --tags"
        echo ""
        echo "🔗 方案3: 使用GitHub CLI"
        echo "gh auth login"
        echo "git push -u origin main"
        echo "git push origin --tags"
        echo ""
        exit 0
        ;;
        
    *)
        print_error "无效选择"
        exit 1
        ;;
esac

echo ""
print_info "🚀 开始推送到 https://github.com/samples28/ggggg..."

# 推送主分支
if git push -u origin main 2>&1; then
    print_success "主分支推送成功"
    
    # 推送标签
    if git push origin --tags 2>&1; then
        print_success "标签推送成功"
    else
        print_warning "标签推送失败，但主分支已推送成功"
    fi
    
    echo ""
    print_success "🎉 推送完成！"
    echo ""
    print_info "📍 仓库访问地址:"
    echo "   https://github.com/samples28/ggggg"
    echo ""
    print_info "📋 推送内容:"
    echo "   - $(git log --oneline | wc -l) 次提交"
    echo "   - $(git tag | wc -l) 个标签"
    echo "   - $(find . -name "*.py" | wc -l) 个Python文件"
    echo "   - $(find . -name "*.md" | wc -l) 个文档文件"
    echo ""
    print_info "🔧 后续操作建议:"
    echo "   1. 访问仓库设置项目描述"
    echo "   2. 添加Topics标签: linux, 2fa, security, sms"
    echo "   3. 启用Issues和Discussions"
    echo "   4. 设置分支保护规则"
    
else
    print_error "推送失败"
    echo ""
    print_info "🔧 可能的解决方案:"
    echo "1. 检查网络连接"
    echo "2. 确认仓库权限"
    echo "3. 验证认证信息"
    echo "4. 查看详细错误信息"
    echo ""
    print_info "📖 详细帮助请查看: PUSH_GUIDE.md"
    exit 1
fi