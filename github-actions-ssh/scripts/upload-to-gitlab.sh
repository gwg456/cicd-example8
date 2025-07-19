#!/bin/bash
# GitLab 仓库上传和 PDF 生成脚本

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

# 配置变量
GITLAB_URL="https://gitlab.com"
PROJECT_NAME="github-actions-ssh-guide"
DEFAULT_BRANCH="main"

# 显示帮助信息
show_help() {
    echo "GitLab 仓库上传和 PDF 生成脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示帮助信息"
    echo "  -u, --username USER     GitLab 用户名"
    echo "  -t, --token TOKEN       GitLab 访问令牌"
    echo "  -p, --project NAME      项目名称 (默认: $PROJECT_NAME)"
    echo "  -b, --branch BRANCH     分支名称 (默认: $DEFAULT_BRANCH)"
    echo "  --gitlab-url URL        GitLab 服务器地址 (默认: $GITLAB_URL)"
    echo "  --generate-pdf          生成 PDF 后再上传"
    echo "  --init-repo             初始化新仓库"
    echo "  --setup-pages           设置 GitLab Pages"
    echo ""
    echo "环境变量:"
    echo "  GITLAB_USERNAME         GitLab 用户名"
    echo "  GITLAB_TOKEN            GitLab 访问令牌"
    echo ""
    echo "示例:"
    echo "  $0 -u myuser -t glpat-xxxx --generate-pdf"
    echo "  $0 --init-repo --setup-pages"
    echo "  GITLAB_TOKEN=glpat-xxxx $0 --generate-pdf"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    local missing=()
    
    if ! command -v git &> /dev/null; then
        missing+=("git")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing+=("curl")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi
    
    if [ ${#missing[@]} -ne 0 ]; then
        print_error "缺少必要依赖: ${missing[*]}"
        print_info "请安装: apt-get install ${missing[*]} 或 brew install ${missing[*]}"
        return 1
    fi
    
    print_success "所有依赖已安装"
}

# 验证 GitLab 凭据
verify_gitlab_credentials() {
    local username="$1"
    local token="$2"
    
    print_info "验证 GitLab 凭据..."
    
    local response=$(curl -s -H "Authorization: Bearer $token" \
                          "$GITLAB_URL/api/v4/user")
    
    if echo "$response" | jq -e .id > /dev/null 2>&1; then
        local gitlab_username=$(echo "$response" | jq -r .username)
        print_success "GitLab 凭据验证成功: $gitlab_username"
        return 0
    else
        print_error "GitLab 凭据验证失败"
        echo "响应: $response"
        return 1
    fi
}

# 检查项目是否存在
check_project_exists() {
    local username="$1"
    local token="$2"
    local project_name="$3"
    
    print_info "检查项目是否存在: $username/$project_name"
    
    local response=$(curl -s -H "Authorization: Bearer $token" \
                          "$GITLAB_URL/api/v4/projects/$username%2F$project_name")
    
    if echo "$response" | jq -e .id > /dev/null 2>&1; then
        print_success "项目已存在"
        return 0
    else
        print_warning "项目不存在"
        return 1
    fi
}

# 创建 GitLab 项目
create_gitlab_project() {
    local username="$1"
    local token="$2"
    local project_name="$3"
    
    print_info "创建 GitLab 项目: $project_name"
    
    local project_data=$(jq -n \
        --arg name "$project_name" \
        --arg desc "GitHub Actions SSH 使用指南 - 完整的 SSH 密钥配置与自动化部署指南" \
        --arg default_branch "$DEFAULT_BRANCH" \
        '{
            name: $name,
            description: $desc,
            visibility: "public",
            issues_enabled: true,
            wiki_enabled: true,
            pages_enabled: true,
            default_branch: $default_branch,
            initialize_with_readme: false
        }')
    
    local response=$(curl -s -X POST \
                          -H "Authorization: Bearer $token" \
                          -H "Content-Type: application/json" \
                          -d "$project_data" \
                          "$GITLAB_URL/api/v4/projects")
    
    if echo "$response" | jq -e .id > /dev/null 2>&1; then
        local project_id=$(echo "$response" | jq -r .id)
        local project_url=$(echo "$response" | jq -r .web_url)
        print_success "项目创建成功"
        print_info "项目 ID: $project_id"
        print_info "项目 URL: $project_url"
        return 0
    else
        print_error "项目创建失败"
        echo "响应: $response"
        return 1
    fi
}

# 生成 PDF 文档
generate_pdf_documents() {
    print_info "生成 PDF 文档..."
    
    # 检查 Python 环境
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 未安装"
        return 1
    fi
    
    # 检查依赖是否安装
    if ! python3 -c "import weasyprint" 2>/dev/null; then
        print_warning "PDF 生成依赖未安装，正在安装..."
        if ! ./scripts/install-dependencies.sh --python-only; then
            print_error "依赖安装失败"
            return 1
        fi
    fi
    
    # 创建输出目录
    mkdir -p output/pdfs
    
    # 生成主要 PDF
    if python3 scripts/generate-pdf.py README.md -o "output/pdfs/GitHub-Actions-SSH-指南.pdf"; then
        print_success "主要 PDF 生成成功"
    else
        print_error "主要 PDF 生成失败"
        return 1
    fi
    
    # 批量生成其他 Markdown 文件
    find . -name "*.md" -not -path "./output/*" -not -path "./.git/*" | while read -r md_file; do
        filename=$(basename "$md_file" .md)
        if [ "$filename" != "README" ]; then
            print_info "生成 PDF: $md_file"
            python3 scripts/generate-pdf.py "$md_file" -o "output/pdfs/${filename}.pdf" || true
        fi
    done
    
    # 显示生成的文件
    print_info "生成的 PDF 文件:"
    ls -la output/pdfs/*.pdf 2>/dev/null || echo "没有 PDF 文件生成"
    
    return 0
}

# 初始化 Git 仓库
init_git_repo() {
    local username="$1"
    local project_name="$2"
    local branch="$3"
    
    print_info "初始化 Git 仓库..."
    
    # 检查是否已经是 Git 仓库
    if [ -d ".git" ]; then
        print_info "已存在 Git 仓库，检查远程配置..."
        
        # 检查是否有 GitLab 远程
        if git remote get-url origin 2>/dev/null | grep -q gitlab; then
            print_info "已配置 GitLab 远程仓库"
        else
            print_info "添加 GitLab 远程仓库..."
            git remote add gitlab "$GITLAB_URL/$username/$project_name.git" || \
            git remote set-url gitlab "$GITLAB_URL/$username/$project_name.git"
        fi
    else
        print_info "初始化新的 Git 仓库..."
        git init
        git remote add origin "$GITLAB_URL/$username/$project_name.git"
    fi
    
    # 设置默认分支
    git checkout -b "$branch" 2>/dev/null || git checkout "$branch" 2>/dev/null || true
    
    print_success "Git 仓库初始化完成"
}

# 提交并推送文件
commit_and_push() {
    local branch="$1"
    
    print_info "提交并推送文件到 GitLab..."
    
    # 添加 .gitignore
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
test-document.*

# Logs
*.log
EOF
    
    # 添加所有文件
    git add .
    
    # 检查是否有更改
    if git diff --staged --quiet; then
        print_warning "没有文件更改，跳过提交"
        return 0
    fi
    
    # 提交更改
    local commit_message="📚 GitHub Actions SSH 使用指南

🎯 主要内容:
- 完整的 SSH 密钥配置指南
- GitHub Actions SSH 自动化部署示例
- PDF 文档生成工具
- GitLab CI/CD 配置

📄 包含文档:
- 基础 SSH 连接示例
- 完整应用部署流程
- 多服务器并行部署
- 数据库备份管理

🛠️ 工具特性:
- 一键 PDF 生成
- 自动化部署脚本
- SSH 密钥管理工具
- 跨平台支持

生成时间: $(date)
提交哈希: $(git rev-parse --short HEAD 2>/dev/null || echo 'initial')"

    git commit -m "$commit_message"
    
    # 推送到 GitLab
    print_info "推送到 GitLab..."
    if git push -u origin "$branch"; then
        print_success "文件推送成功"
    else
        print_error "文件推送失败"
        return 1
    fi
}

# 启用 GitLab Pages
enable_gitlab_pages() {
    local username="$1"
    local token="$2"
    local project_name="$3"
    
    print_info "启用 GitLab Pages..."
    
    # 获取项目 ID
    local project_response=$(curl -s -H "Authorization: Bearer $token" \
                                  "$GITLAB_URL/api/v4/projects/$username%2F$project_name")
    
    local project_id=$(echo "$project_response" | jq -r .id)
    
    if [ "$project_id" = "null" ]; then
        print_error "无法获取项目 ID"
        return 1
    fi
    
    # 启用 Pages
    local pages_response=$(curl -s -X PUT \
                                -H "Authorization: Bearer $token" \
                                -H "Content-Type: application/json" \
                                -d '{"pages_access_level": "public"}' \
                                "$GITLAB_URL/api/v4/projects/$project_id")
    
    print_success "GitLab Pages 配置完成"
    print_info "Pages URL: https://$username.gitlab.io/$project_name"
}

# 创建 GitLab 发布
create_gitlab_release() {
    local username="$1"
    local token="$2"
    local project_name="$3"
    
    print_info "创建 GitLab 发布..."
    
    # 获取项目 ID
    local project_response=$(curl -s -H "Authorization: Bearer $token" \
                                  "$GITLAB_URL/api/v4/projects/$username%2F$project_name")
    
    local project_id=$(echo "$project_response" | jq -r .id)
    local commit_sha=$(git rev-parse HEAD)
    local version="v$(date +%Y%m%d-%H%M%S)"
    
    # 生成发布说明
    local release_notes="# GitHub Actions SSH 使用指南 $version

## 📄 文档内容

这是一个完整的 GitHub Actions SSH 使用指南，包含以下内容：

### 🔑 SSH 密钥配置
- SSH 密钥生成和管理
- 服务器配置和安全设置
- GitHub Secrets 配置指南

### 🚀 自动化部署示例
- 基础 SSH 连接示例
- 完整应用部署流程
- 多服务器并行部署
- 数据库备份和管理

### 🛠️ 工具和脚本
- PDF 文档生成工具
- SSH 密钥设置助手
- 批量部署脚本
- GitLab CI/CD 配置

## 📦 下载链接

- [📚 在线文档](https://$username.gitlab.io/$project_name)
- [📄 PDF 下载](https://$username.gitlab.io/$project_name/pdfs/GitHub-Actions-SSH-指南.pdf)

## 📊 统计信息

- 生成时间: $(date)
- 提交哈希: ${commit_sha:0:8}
- 包含文件: $(find . -name "*.md" -o -name "*.py" -o -name "*.sh" | wc -l) 个
"

    # 创建发布
    local release_data=$(jq -n \
        --arg tag "$version" \
        --arg name "GitHub Actions SSH 指南 $version" \
        --arg desc "$release_notes" \
        --arg ref "$commit_sha" \
        '{
            tag_name: $tag,
            name: $name,
            description: $desc,
            ref: $ref
        }')
    
    local release_response=$(curl -s -X POST \
                                  -H "Authorization: Bearer $token" \
                                  -H "Content-Type: application/json" \
                                  -d "$release_data" \
                                  "$GITLAB_URL/api/v4/projects/$project_id/releases")
    
    if echo "$release_response" | jq -e .tag_name > /dev/null 2>&1; then
        local release_url=$(echo "$release_response" | jq -r ._links.self)
        print_success "发布创建成功: $version"
        print_info "发布链接: $release_url"
    else
        print_warning "发布创建失败（可能是权限问题）"
        echo "响应: $release_response"
    fi
}

# 显示项目信息
show_project_info() {
    local username="$1"
    local project_name="$2"
    
    print_success "🎉 项目上传完成！"
    echo ""
    print_info "📁 项目信息:"
    echo "  - 仓库地址: $GITLAB_URL/$username/$project_name"
    echo "  - Pages 地址: https://$username.gitlab.io/$project_name"
    echo "  - 克隆地址: git clone $GITLAB_URL/$username/$project_name.git"
    echo ""
    print_info "📄 文档访问:"
    echo "  - 在线阅读: https://$username.gitlab.io/$project_name"
    echo "  - PDF 下载: https://$username.gitlab.io/$project_name/pdfs/"
    echo ""
    print_info "🔧 后续步骤:"
    echo "  1. 访问项目页面配置 CI/CD 变量（如果需要）"
    echo "  2. 等待 GitLab Pages 部署完成（通常几分钟）"
    echo "  3. 查看生成的 PDF 文档"
    echo "  4. 根据需要调整 GitLab CI/CD 配置"
}

# 主函数
main() {
    local username=""
    local token=""
    local project_name="$PROJECT_NAME"
    local branch="$DEFAULT_BRANCH"
    local generate_pdf=false
    local init_repo=false
    local setup_pages=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -u|--username)
                username="$2"
                shift 2
                ;;
            -t|--token)
                token="$2"
                shift 2
                ;;
            -p|--project)
                project_name="$2"
                shift 2
                ;;
            -b|--branch)
                branch="$2"
                shift 2
                ;;
            --gitlab-url)
                GITLAB_URL="$2"
                shift 2
                ;;
            --generate-pdf)
                generate_pdf=true
                shift
                ;;
            --init-repo)
                init_repo=true
                shift
                ;;
            --setup-pages)
                setup_pages=true
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 从环境变量获取凭据
    username=${username:-$GITLAB_USERNAME}
    token=${token:-$GITLAB_TOKEN}
    
    # 检查必需参数
    if [ -z "$username" ] || [ -z "$token" ]; then
        print_error "缺少 GitLab 用户名或访问令牌"
        print_info "请使用 -u/--username 和 -t/--token 参数，或设置环境变量 GITLAB_USERNAME 和 GITLAB_TOKEN"
        exit 1
    fi
    
    print_info "🚀 开始 GitLab 项目设置和 PDF 生成..."
    echo ""
    
    # 检查依赖
    check_dependencies || exit 1
    echo ""
    
    # 验证凭据
    verify_gitlab_credentials "$username" "$token" || exit 1
    echo ""
    
    # 生成 PDF（如果请求）
    if [ "$generate_pdf" = true ]; then
        generate_pdf_documents || exit 1
        echo ""
    fi
    
    # 检查并创建项目
    if ! check_project_exists "$username" "$token" "$project_name"; then
        if [ "$init_repo" = true ]; then
            create_gitlab_project "$username" "$token" "$project_name" || exit 1
            echo ""
        else
            print_error "项目不存在，请使用 --init-repo 参数创建新项目"
            exit 1
        fi
    fi
    
    # 初始化和推送仓库
    init_git_repo "$username" "$project_name" "$branch" || exit 1
    echo ""
    
    commit_and_push "$branch" || exit 1
    echo ""
    
    # 设置 GitLab Pages
    if [ "$setup_pages" = true ]; then
        enable_gitlab_pages "$username" "$token" "$project_name" || exit 1
        echo ""
    fi
    
    # 创建发布
    create_gitlab_release "$username" "$token" "$project_name" || true
    echo ""
    
    # 显示项目信息
    show_project_info "$username" "$project_name"
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi