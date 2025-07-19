#!/bin/bash
# Linux SMS 2FA 安装脚本

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
INSTALL_DIR="/opt/sms-2fa"
CONFIG_DIR="/etc/sms-2fa"
LOG_DIR="/var/log/sms-2fa"
BIN_DIR="/usr/local/bin"
SYSTEMD_DIR="/etc/systemd/system"
PAM_DIR="/lib/security"
SERVICE_USER="sms-2fa"

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要root权限运行"
        print_info "请使用: sudo $0"
        exit 1
    fi
}

# 检查系统支持
check_system() {
    print_info "检查系统兼容性..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        print_error "无法确定操作系统版本"
        exit 1
    fi
    
    source /etc/os-release
    print_info "检测到系统: $NAME $VERSION"
    
    # 检查架构
    ARCH=$(uname -m)
    print_info "系统架构: $ARCH"
    
    # 检查systemd
    if ! command -v systemctl &> /dev/null; then
        print_warning "未检测到systemd，服务管理功能可能不可用"
    fi
    
    # 检查PAM
    if [[ ! -d /etc/pam.d ]]; then
        print_error "未检测到PAM，无法集成认证功能"
        exit 1
    fi
    
    print_success "系统兼容性检查通过"
}

# 安装系统依赖
install_dependencies() {
    print_info "安装系统依赖..."
    
    # 检测包管理器
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev \
            build-essential \
            libpam-python \
            libpam-modules \
            curl \
            jq \
            systemd
            
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        yum update -y
        yum install -y \
            python3 \
            python3-pip \
            python3-devel \
            gcc \
            gcc-c++ \
            make \
            pam-devel \
            curl \
            jq \
            systemd
            
    elif command -v dnf &> /dev/null; then
        # Fedora
        dnf update -y
        dnf install -y \
            python3 \
            python3-pip \
            python3-devel \
            gcc \
            gcc-c++ \
            make \
            pam-devel \
            curl \
            jq \
            systemd
            
    elif command -v zypper &> /dev/null; then
        # openSUSE
        zypper refresh
        zypper install -y \
            python3 \
            python3-pip \
            python3-devel \
            gcc \
            gcc-c++ \
            make \
            pam-devel \
            curl \
            jq \
            systemd
            
    else
        print_error "未支持的包管理器，请手动安装依赖"
        print_info "需要安装: python3, python3-pip, python3-dev, build-essential, libpam-python"
        exit 1
    fi
    
    print_success "系统依赖安装完成"
}

# 创建系统用户
create_user() {
    print_info "创建系统用户..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d /var/lib/sms-2fa -c "SMS 2FA Service" $SERVICE_USER
        print_success "用户 $SERVICE_USER 创建成功"
    else
        print_info "用户 $SERVICE_USER 已存在"
    fi
}

# 创建目录结构
create_directories() {
    print_info "创建目录结构..."
    
    # 创建主要目录
    mkdir -p $INSTALL_DIR
    mkdir -p $CONFIG_DIR
    mkdir -p $LOG_DIR
    mkdir -p /var/lib/sms-2fa
    
    # 设置权限
    chown root:root $INSTALL_DIR
    chmod 755 $INSTALL_DIR
    
    chown root:$SERVICE_USER $CONFIG_DIR
    chmod 750 $CONFIG_DIR
    
    chown $SERVICE_USER:$SERVICE_USER $LOG_DIR
    chmod 750 $LOG_DIR
    
    chown $SERVICE_USER:$SERVICE_USER /var/lib/sms-2fa
    chmod 750 /var/lib/sms-2fa
    
    print_success "目录结构创建完成"
}

# 安装Python依赖
install_python_deps() {
    print_info "安装Python依赖..."
    
    # 创建虚拟环境
    if [[ ! -d $INSTALL_DIR/venv ]]; then
        python3 -m venv $INSTALL_DIR/venv
        print_success "Python虚拟环境创建完成"
    fi
    
    # 激活虚拟环境并安装依赖
    source $INSTALL_DIR/venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装requirements
    if [[ -f requirements.txt ]]; then
        pip install -r requirements.txt
        print_success "Python依赖安装完成"
    else
        print_warning "requirements.txt 文件未找到，请手动安装Python依赖"
    fi
    
    deactivate
}

# 复制文件
copy_files() {
    print_info "复制程序文件..."
    
    # 复制源代码
    cp -r src/ $INSTALL_DIR/
    cp -r pam/ $INSTALL_DIR/
    cp -r scripts/ $INSTALL_DIR/
    
    # 复制配置文件
    if [[ -f config/2fa.conf ]]; then
        cp config/2fa.conf $CONFIG_DIR/2fa.conf.example
        if [[ ! -f $CONFIG_DIR/2fa.conf ]]; then
            cp config/2fa.conf $CONFIG_DIR/2fa.conf
        fi
    fi
    
    if [[ -f config/users.conf ]]; then
        cp config/users.conf $CONFIG_DIR/users.conf.example
        if [[ ! -f $CONFIG_DIR/users.conf ]]; then
            cp config/users.conf $CONFIG_DIR/users.conf
        fi
    fi
    
    # 设置权限
    chown -R root:root $INSTALL_DIR/src
    chown -R root:root $INSTALL_DIR/pam
    chown -R root:root $INSTALL_DIR/scripts
    chmod -R 755 $INSTALL_DIR/scripts
    
    chown root:$SERVICE_USER $CONFIG_DIR/*.conf
    chmod 640 $CONFIG_DIR/*.conf
    
    print_success "程序文件复制完成"
}

# 创建命令行工具
create_cli_tools() {
    print_info "创建命令行工具..."
    
    # SMS 2FA 管理工具
    cat > $BIN_DIR/sms-2fa << 'EOF'
#!/bin/bash
# SMS 2FA 管理工具
INSTALL_DIR="/opt/sms-2fa"
source $INSTALL_DIR/venv/bin/activate
python3 $INSTALL_DIR/scripts/user_manager.py "$@"
EOF
    
    # PAM模块测试工具
    cat > $BIN_DIR/sms-2fa-test << 'EOF'
#!/bin/bash
# SMS 2FA PAM模块测试工具
INSTALL_DIR="/opt/sms-2fa"
source $INSTALL_DIR/venv/bin/activate
python3 $INSTALL_DIR/pam/pam_sms_2fa.py "$@"
EOF
    
    # 短信测试工具
    cat > $BIN_DIR/sms-2fa-send << 'EOF'
#!/bin/bash
# SMS 2FA 短信发送测试工具
INSTALL_DIR="/opt/sms-2fa"
source $INSTALL_DIR/venv/bin/activate
python3 $INSTALL_DIR/scripts/test_sms.py "$@"
EOF
    
    # 设置权限
    chmod 755 $BIN_DIR/sms-2fa
    chmod 755 $BIN_DIR/sms-2fa-test
    chmod 755 $BIN_DIR/sms-2fa-send
    
    print_success "命令行工具创建完成"
}

# 配置systemd服务
configure_systemd() {
    print_info "配置systemd服务..."
    
    # 创建服务文件
    cat > $SYSTEMD_DIR/sms-2fa.service << EOF
[Unit]
Description=SMS Two-Factor Authentication Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python -m src.sms_2fa
Restart=always
RestartSec=10

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR $CONFIG_DIR /var/lib/sms-2fa

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    systemctl daemon-reload
    
    print_success "systemd服务配置完成"
}

# 配置PAM
configure_pam() {
    print_info "配置PAM集成..."
    
    # 创建PAM模块链接
    if [[ -d $PAM_DIR ]]; then
        ln -sf $INSTALL_DIR/pam/pam_sms_2fa.py $PAM_DIR/pam_sms_2fa.py
        chmod 755 $PAM_DIR/pam_sms_2fa.py
        
        print_success "PAM模块配置完成"
        print_warning "请手动编辑 /etc/pam.d/ 中的相关文件以启用SMS 2FA"
        print_info "示例配置："
        print_info "  auth required pam_sms_2fa.py"
    else
        print_warning "PAM目录未找到，跳过PAM配置"
    fi
}

# 配置日志轮转
configure_logrotate() {
    print_info "配置日志轮转..."
    
    cat > /etc/logrotate.d/sms-2fa << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload sms-2fa.service > /dev/null 2>&1 || true
    endscript
}
EOF
    
    print_success "日志轮转配置完成"
}

# 生成示例配置
generate_config() {
    print_info "生成配置文件..."
    
    # 如果配置文件不存在，创建示例配置
    if [[ ! -f $CONFIG_DIR/2fa.conf ]]; then
        cat > $CONFIG_DIR/2fa.conf << 'EOF'
[aliyun]
access_key_id = YOUR_ACCESS_KEY_ID
access_key_secret = YOUR_ACCESS_KEY_SECRET
region = cn-hangzhou
sign_name = 您的签名
template_code = SMS_123456789

[sms]
code_expire_time = 300
code_length = 6
max_send_per_minute = 3
max_verify_attempts = 5

[system]
log_level = INFO
log_file = /var/log/sms-2fa/sms-2fa.log
enable_redis = false
redis_host = localhost
redis_port = 6379
redis_db = 0
redis_password = 

[security]
enable_encryption = true
fail_delay = 3
max_login_attempts = 5
lockout_duration = 1800

[pam]
service_name = sms-2fa
enable_bypass_users = true
bypass_users = root

[audit]
enable_audit_log = true
audit_log_file = /var/log/sms-2fa/audit.log
audit_log_level = INFO
EOF
        
        chown root:$SERVICE_USER $CONFIG_DIR/2fa.conf
        chmod 640 $CONFIG_DIR/2fa.conf
    fi
    
    # 创建用户配置文件
    if [[ ! -f $CONFIG_DIR/users.conf ]]; then
        cat > $CONFIG_DIR/users.conf << 'EOF'
[users]
# 格式: username = phone_number
# 示例: admin = +8613812345678
EOF
        
        chown root:$SERVICE_USER $CONFIG_DIR/users.conf
        chmod 640 $CONFIG_DIR/users.conf
    fi
    
    print_success "配置文件生成完成"
}

# 验证安装
verify_installation() {
    print_info "验证安装..."
    
    local errors=0
    
    # 检查文件
    if [[ ! -f $INSTALL_DIR/src/sms_2fa.py ]]; then
        print_error "主程序文件缺失"
        errors=$((errors + 1))
    fi
    
    if [[ ! -f $CONFIG_DIR/2fa.conf ]]; then
        print_error "配置文件缺失"
        errors=$((errors + 1))
    fi
    
    if [[ ! -f $BIN_DIR/sms-2fa ]]; then
        print_error "命令行工具缺失"
        errors=$((errors + 1))
    fi
    
    # 检查Python依赖
    if ! $INSTALL_DIR/venv/bin/python -c "import alibabacloud_dysmsapi20170525" 2>/dev/null; then
        print_error "阿里云SDK未正确安装"
        errors=$((errors + 1))
    fi
    
    # 检查权限
    if [[ ! -r $CONFIG_DIR/2fa.conf ]]; then
        print_error "配置文件权限错误"
        errors=$((errors + 1))
    fi
    
    if [[ $errors -eq 0 ]]; then
        print_success "安装验证通过"
        return 0
    else
        print_error "发现 $errors 个错误"
        return 1
    fi
}

# 显示安装后信息
show_post_install_info() {
    print_success "🎉 SMS 2FA 安装完成！"
    echo ""
    print_info "📁 安装信息:"
    echo "  - 安装目录: $INSTALL_DIR"
    echo "  - 配置目录: $CONFIG_DIR"
    echo "  - 日志目录: $LOG_DIR"
    echo "  - 服务用户: $SERVICE_USER"
    echo ""
    print_info "🔧 命令行工具:"
    echo "  - sms-2fa: 用户管理工具"
    echo "  - sms-2fa-test: PAM模块测试工具"
    echo "  - sms-2fa-send: 短信发送测试工具"
    echo ""
    print_info "⚙️  配置步骤:"
    echo "  1. 编辑配置文件: $CONFIG_DIR/2fa.conf"
    echo "  2. 配置阿里云短信服务凭据"
    echo "  3. 添加用户手机号: sms-2fa add username phone_number"
    echo "  4. 测试短信发送: sms-2fa-send test username"
    echo "  5. 配置PAM: 编辑 /etc/pam.d/ 文件"
    echo ""
    print_info "🚀 启动服务:"
    echo "  - systemctl enable sms-2fa"
    echo "  - systemctl start sms-2fa"
    echo ""
    print_warning "⚠️  重要提醒:"
    echo "  - 请务必配置阿里云短信服务凭据"
    echo "  - 建议在生产环境前进行充分测试"
    echo "  - 定期备份配置文件"
    echo ""
    print_info "📖 文档和支持:"
    echo "  - 配置说明: 查看 $CONFIG_DIR/ 目录下的示例文件"
    echo "  - 故障排除: 查看 $LOG_DIR/ 目录下的日志文件"
}

# 主函数
main() {
    echo "🔐 Linux SMS 2FA 双重因子认证系统安装程序"
    echo "================================================"
    echo ""
    
    # 检查参数
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h     显示帮助信息"
        echo "  --uninstall    卸载SMS 2FA"
        echo ""
        exit 0
    fi
    
    if [[ "$1" == "--uninstall" ]]; then
        print_info "开始卸载SMS 2FA..."
        
        # 停止服务
        systemctl stop sms-2fa.service 2>/dev/null || true
        systemctl disable sms-2fa.service 2>/dev/null || true
        
        # 删除文件
        rm -rf $INSTALL_DIR
        rm -f $BIN_DIR/sms-2fa
        rm -f $BIN_DIR/sms-2fa-test
        rm -f $BIN_DIR/sms-2fa-send
        rm -f $SYSTEMD_DIR/sms-2fa.service
        rm -f $PAM_DIR/pam_sms_2fa.py
        rm -f /etc/logrotate.d/sms-2fa
        
        # 重新加载systemd
        systemctl daemon-reload
        
        print_success "SMS 2FA 卸载完成"
        print_warning "配置文件和日志文件保留在 $CONFIG_DIR 和 $LOG_DIR"
        exit 0
    fi
    
    # 执行安装步骤
    check_root
    check_system
    install_dependencies
    create_user
    create_directories
    copy_files
    install_python_deps
    create_cli_tools
    configure_systemd
    configure_pam
    configure_logrotate
    generate_config
    
    # 验证安装
    if verify_installation; then
        show_post_install_info
        exit 0
    else
        print_error "安装过程中发现错误，请检查日志"
        exit 1
    fi
}

# 运行主函数
main "$@"