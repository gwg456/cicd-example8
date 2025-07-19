#!/bin/bash
# GitHub Actions SSH 密钥设置脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数：打印彩色信息
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

# 检查必需的工具
check_requirements() {
    print_info "检查必需的工具..."
    
    local missing_tools=()
    
    if ! command -v ssh-keygen &> /dev/null; then
        missing_tools+=("ssh-keygen")
    fi
    
    if ! command -v ssh-copy-id &> /dev/null; then
        missing_tools+=("ssh-copy-id")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "缺少必需的工具: ${missing_tools[*]}"
        print_info "请安装: apt-get install openssh-client 或 yum install openssh-clients"
        exit 1
    fi
    
    print_success "所有必需工具已安装"
}

# 生成 SSH 密钥对
generate_ssh_key() {
    local key_name="$1"
    local email="$2"
    
    print_info "生成 SSH 密钥对: $key_name"
    
    if [ -f "$HOME/.ssh/$key_name" ]; then
        print_warning "密钥 $key_name 已存在"
        read -p "是否覆盖? (y/N): " overwrite
        if [[ ! $overwrite =~ ^[Yy]$ ]]; then
            print_info "跳过密钥生成"
            return 0
        fi
    fi
    
    # 生成 ed25519 密钥（推荐）
    ssh-keygen -t ed25519 -C "$email" -f "$HOME/.ssh/$key_name" -N ""
    
    print_success "SSH 密钥对已生成"
    print_info "私钥: $HOME/.ssh/$key_name"
    print_info "公钥: $HOME/.ssh/$key_name.pub"
}

# 显示公钥内容
show_public_key() {
    local key_name="$1"
    local public_key_file="$HOME/.ssh/$key_name.pub"
    
    if [ ! -f "$public_key_file" ]; then
        print_error "公钥文件不存在: $public_key_file"
        return 1
    fi
    
    print_info "公钥内容 ($key_name.pub):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "$public_key_file"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 显示私钥内容（用于 GitHub Secrets）
show_private_key() {
    local key_name="$1"
    local private_key_file="$HOME/.ssh/$key_name"
    
    if [ ! -f "$private_key_file" ]; then
        print_error "私钥文件不存在: $private_key_file"
        return 1
    fi
    
    print_warning "私钥内容 ($key_name) - 请妥善保管！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "$private_key_file"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 复制公钥到服务器
copy_key_to_server() {
    local key_name="$1"
    local server="$2"
    local user="$3"
    
    print_info "复制公钥到服务器: $user@$server"
    
    if ssh-copy-id -i "$HOME/.ssh/$key_name.pub" "$user@$server"; then
        print_success "公钥已复制到 $user@$server"
    else
        print_error "复制公钥失败"
        print_info "手动复制方法:"
        echo "cat $HOME/.ssh/$key_name.pub | ssh $user@$server \"mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys\""
        return 1
    fi
}

# 测试 SSH 连接
test_ssh_connection() {
    local key_name="$1"
    local server="$2"
    local user="$3"
    
    print_info "测试 SSH 连接: $user@$server"
    
    if ssh -i "$HOME/.ssh/$key_name" -o PasswordAuthentication=no -o ConnectTimeout=10 "$user@$server" "echo '连接成功'" 2>/dev/null; then
        print_success "SSH 连接测试通过"
    else
        print_error "SSH 连接测试失败"
        print_info "请检查:"
        echo "  1. 服务器地址和用户名是否正确"
        echo "  2. 公钥是否正确添加到服务器"
        echo "  3. SSH 服务是否运行"
        echo "  4. 防火墙设置"
        return 1
    fi
}

# 生成 known_hosts 条目
generate_known_hosts() {
    local server="$1"
    local port="${2:-22}"
    
    print_info "生成 known_hosts 条目: $server:$port"
    
    ssh-keyscan -p "$port" "$server" 2>/dev/null || {
        print_error "无法获取服务器指纹"
        return 1
    }
}

# 显示 GitHub Secrets 配置指南
show_github_secrets_guide() {
    local key_name="$1"
    local server="$2"
    local user="$3"
    local port="${4:-22}"
    
    print_info "GitHub Secrets 配置指南"
    echo ""
    echo "在 GitHub 仓库中设置以下 Secrets:"
    echo ""
    
    echo "1️⃣  SSH_PRIVATE_KEY:"
    show_private_key "$key_name"
    echo ""
    
    echo "2️⃣  SSH_HOST:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$server"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "3️⃣  SSH_USERNAME:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$user"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "4️⃣  SSH_PORT:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$port"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "5️⃣  KNOWN_HOSTS (可选):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    generate_known_hosts "$server" "$port"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 主菜单
show_menu() {
    echo ""
    print_info "GitHub Actions SSH 密钥设置工具"
    echo ""
    echo "1) 生成新的 SSH 密钥对"
    echo "2) 显示公钥内容"
    echo "3) 显示私钥内容"
    echo "4) 复制公钥到服务器"
    echo "5) 测试 SSH 连接"
    echo "6) 生成 known_hosts 条目"
    echo "7) 显示 GitHub Secrets 配置指南"
    echo "8) 一键设置流程"
    echo "9) 退出"
    echo ""
}

# 一键设置流程
quick_setup() {
    print_info "开始一键设置流程"
    
    # 获取用户输入
    read -p "请输入密钥名称 (默认: github_actions): " key_name
    key_name=${key_name:-github_actions}
    
    read -p "请输入邮箱地址: " email
    if [ -z "$email" ]; then
        print_error "邮箱地址不能为空"
        return 1
    fi
    
    read -p "请输入服务器地址: " server
    if [ -z "$server" ]; then
        print_error "服务器地址不能为空"
        return 1
    fi
    
    read -p "请输入用户名: " user
    if [ -z "$user" ]; then
        print_error "用户名不能为空"
        return 1
    fi
    
    read -p "请输入 SSH 端口 (默认: 22): " port
    port=${port:-22}
    
    # 执行设置步骤
    echo ""
    print_info "执行设置步骤..."
    
    # 1. 生成密钥
    generate_ssh_key "$key_name" "$email" || return 1
    
    # 2. 复制到服务器
    copy_key_to_server "$key_name" "$server" "$user" || {
        print_warning "自动复制失败，请手动复制公钥"
        show_public_key "$key_name"
        read -p "完成手动复制后按 Enter 继续..."
    }
    
    # 3. 测试连接
    test_ssh_connection "$key_name" "$server" "$user" || return 1
    
    # 4. 显示配置指南
    show_github_secrets_guide "$key_name" "$server" "$user" "$port"
    
    print_success "一键设置完成！"
}

# 主函数
main() {
    check_requirements
    
    while true; do
        show_menu
        read -p "请选择操作 (1-9): " choice
        
        case $choice in
            1)
                read -p "请输入密钥名称: " key_name
                read -p "请输入邮箱地址: " email
                generate_ssh_key "$key_name" "$email"
                ;;
            2)
                read -p "请输入密钥名称: " key_name
                show_public_key "$key_name"
                ;;
            3)
                read -p "请输入密钥名称: " key_name
                show_private_key "$key_name"
                ;;
            4)
                read -p "请输入密钥名称: " key_name
                read -p "请输入服务器地址: " server
                read -p "请输入用户名: " user
                copy_key_to_server "$key_name" "$server" "$user"
                ;;
            5)
                read -p "请输入密钥名称: " key_name
                read -p "请输入服务器地址: " server
                read -p "请输入用户名: " user
                test_ssh_connection "$key_name" "$server" "$user"
                ;;
            6)
                read -p "请输入服务器地址: " server
                read -p "请输入端口 (默认 22): " port
                port=${port:-22}
                generate_known_hosts "$server" "$port"
                ;;
            7)
                read -p "请输入密钥名称: " key_name
                read -p "请输入服务器地址: " server
                read -p "请输入用户名: " user
                read -p "请输入端口 (默认 22): " port
                port=${port:-22}
                show_github_secrets_guide "$key_name" "$server" "$user" "$port"
                ;;
            8)
                quick_setup
                ;;
            9)
                print_success "再见！"
                break
                ;;
            *)
                print_error "无效的选择，请输入 1-9"
                ;;
        esac
        
        echo ""
        read -p "按 Enter 继续..."
    done
}

# 如果脚本被直接执行，运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi