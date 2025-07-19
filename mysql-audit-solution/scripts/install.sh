#!/bin/bash
# MySQL 审计解决方案一键安装脚本
# 基于 MariaDB Audit Plugin 的生产环境部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
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

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要root权限运行"
        print_info "请使用: sudo $0"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        print_error "无法检测操作系统"
        exit 1
    fi
    
    print_info "检测到操作系统: $OS $OS_VERSION"
}

# 检测MySQL版本
detect_mysql_version() {
    if command -v mysql >/dev/null 2>&1; then
        MYSQL_VERSION_FULL=$(mysql --version | awk '{print $5}' | awk -F, '{print $1}')
        MYSQL_MAJOR_VERSION=$(echo $MYSQL_VERSION_FULL | cut -d. -f1)
        MYSQL_MINOR_VERSION=$(echo $MYSQL_VERSION_FULL | cut -d. -f2)
        MYSQL_VERSION="${MYSQL_MAJOR_VERSION}.${MYSQL_MINOR_VERSION}"
        
        print_info "检测到MySQL版本: $MYSQL_VERSION_FULL"
        
        # 检查版本兼容性
        case $MYSQL_VERSION in
            "5.6"|"5.7"|"8.0")
                print_success "MySQL版本 $MYSQL_VERSION 受支持"
                return 0
                ;;
            "5.5")
                print_warning "MySQL 5.5版本功能有限，建议升级到5.6+"
                return 0
                ;;
            *)
                print_error "不支持的MySQL版本: $MYSQL_VERSION"
                print_info "支持的版本: 5.6, 5.7, 8.0"
                return 1
                ;;
        esac
    else
        print_error "未检测到MySQL，请先安装MySQL"
        return 1
    fi
}

# 安装系统依赖
install_dependencies() {
    print_info "安装系统依赖..."
    
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                curl \
                wget \
                unzip \
                logrotate \
                systemd
            ;;
        centos|rhel|rocky|almalinux)
            yum update -y
            yum install -y \
                python3 \
                python3-pip \
                curl \
                wget \
                unzip \
                logrotate \
                systemd
            ;;
        *)
            print_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
    
    print_success "系统依赖安装完成"
}

# 下载MariaDB审计插件
download_audit_plugin() {
    print_info "下载MariaDB审计插件..."
    
    # 获取MySQL插件目录
    PLUGIN_DIR=$(mysql -e "SHOW VARIABLES LIKE 'plugin_dir';" | grep plugin_dir | awk '{print $2}')
    
    if [[ -z "$PLUGIN_DIR" ]]; then
        PLUGIN_DIR="/usr/lib/mysql/plugin"
        print_warning "无法获取插件目录，使用默认路径: $PLUGIN_DIR"
    fi
    
    print_info "MySQL插件目录: $PLUGIN_DIR"
    
    # 检测系统架构
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            PLUGIN_ARCH="linux-x86_64"
            ;;
        aarch64)
            PLUGIN_ARCH="linux-aarch64"
            ;;
        *)
            print_error "不支持的系统架构: $ARCH"
            exit 1
            ;;
    esac
    
    # 根据MySQL版本选择合适的插件
    PLUGIN_FILE="server_audit.so"
    case $MYSQL_VERSION in
        "5.6")
            PLUGIN_URL="https://downloads.mariadb.org/f/audit-plugin-mysql-5.6/server_audit-1.4.7-${PLUGIN_ARCH}.so"
            print_info "使用MySQL 5.6兼容的审计插件"
            ;;
        "5.7")
            PLUGIN_URL="https://downloads.mariadb.org/f/audit-plugin-mysql-5.7/server_audit-1.4.7-${PLUGIN_ARCH}.so"
            print_info "使用MySQL 5.7兼容的审计插件"
            ;;
        "8.0")
            # 对于MySQL 8.0，可能需要使用AWS的audit plugin
            PLUGIN_URL="https://github.com/aws/audit-plugin-for-mysql/releases/download/v1.0.0/server_audit-${PLUGIN_ARCH}.so"
            print_info "使用MySQL 8.0兼容的审计插件"
            ;;
        *)
            PLUGIN_URL="https://downloads.mariadb.org/f/audit-plugin-mysql-5.7/server_audit-1.4.7-${PLUGIN_ARCH}.so"
            print_warning "使用通用审计插件版本"
            ;;
    esac
    
    mkdir -p plugins
    
    if [[ ! -f "plugins/${PLUGIN_FILE}" ]]; then
        print_info "从远程下载审计插件..."
        print_info "下载地址: $PLUGIN_URL"
        
        # 尝试下载插件
        if ! wget -O "plugins/${PLUGIN_FILE}" "$PLUGIN_URL" 2>/dev/null; then
            print_warning "自动下载失败，尝试本地预置插件..."
            
            # 如果下载失败，创建一个占位文件提示用户手动下载
            cat > "plugins/DOWNLOAD_INSTRUCTIONS.txt" << EOF
审计插件下载说明：

请手动下载适用于MySQL ${MYSQL_VERSION}的server_audit.so插件：

1. 访问 MariaDB 官方下载页面：
   https://downloads.mariadb.org/

2. 选择对应版本的插件：
   - MySQL 5.6: https://downloads.mariadb.org/f/audit-plugin-mysql-5.6/
   - MySQL 5.7: https://downloads.mariadb.org/f/audit-plugin-mysql-5.7/
   
3. 下载适用于 ${PLUGIN_ARCH} 架构的插件

4. 将插件文件重命名为 server_audit.so 并放置到：
   ${PLUGIN_DIR}/

5. 设置正确的权限：
   chmod 755 ${PLUGIN_DIR}/server_audit.so
   chown mysql:mysql ${PLUGIN_DIR}/server_audit.so

6. 重新运行安装脚本
EOF
            print_error "无法自动下载插件，请查看 plugins/DOWNLOAD_INSTRUCTIONS.txt"
            print_info "或者手动将 server_audit.so 放置到 plugins/ 目录"
            return 1
        fi
    fi
    
    # 验证插件文件
    if [[ ! -f "plugins/${PLUGIN_FILE}" ]] || [[ ! -s "plugins/${PLUGIN_FILE}" ]]; then
        print_error "插件文件无效或不存在"
        return 1
    fi
    
    # 复制插件到MySQL插件目录
    cp "plugins/${PLUGIN_FILE}" "$PLUGIN_DIR/"
    chmod 755 "$PLUGIN_DIR/${PLUGIN_FILE}"
    chown mysql:mysql "$PLUGIN_DIR/${PLUGIN_FILE}" 2>/dev/null || true
    
    print_success "审计插件安装完成"
}

# 配置MySQL
configure_mysql() {
    print_info "配置MySQL审计..."
    
    # 备份MySQL配置文件
    MYSQL_CNF=""
    for cnf in /etc/mysql/mysql.conf.d/mysqld.cnf /etc/my.cnf /etc/mysql/my.cnf; do
        if [[ -f "$cnf" ]]; then
            MYSQL_CNF="$cnf"
            break
        fi
    done
    
    if [[ -z "$MYSQL_CNF" ]]; then
        print_error "未找到MySQL配置文件"
        exit 1
    fi
    
    print_info "使用MySQL配置文件: $MYSQL_CNF"
    
    # 备份原配置
    cp "$MYSQL_CNF" "${MYSQL_CNF}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # 检查是否已配置审计
    if ! grep -q "server_audit" "$MYSQL_CNF"; then
        print_info "添加审计配置到MySQL ${MYSQL_VERSION}..."
        
        # 根据MySQL版本使用不同的配置
        case $MYSQL_VERSION in
            "5.6")
                cat >> "$MYSQL_CNF" << 'EOF'

# ================================
# MySQL 5.6 审计配置 - MariaDB Plugin
# ================================
# 加载审计插件
plugin-load-add=server_audit.so

# 基础配置
server_audit_logging=ON
server_audit_output_type=file
server_audit_file_path=/var/log/mysql/audit.log
server_audit_file_rotate_size=100000000
server_audit_file_rotations=10

# 审计事件类型（5.6版本支持的事件类型）
server_audit_events=CONNECT,QUERY

# 用户过滤（排除系统用户）
server_audit_excl_users=

# 性能优化
server_audit_syslog_priority=LOG_INFO

# MySQL 5.6 特定配置
server_audit_incl_users=
EOF
                ;;
            "5.7")
                cat >> "$MYSQL_CNF" << 'EOF'

# ================================
# MySQL 5.7 审计配置 - MariaDB Plugin
# ================================
# 加载审计插件
plugin-load-add=server_audit.so

# 基础配置
server_audit_logging=ON
server_audit_output_type=file
server_audit_file_path=/var/log/mysql/audit.log
server_audit_file_rotate_size=100000000
server_audit_file_rotations=10

# 审计事件类型
server_audit_events=CONNECT,QUERY,TABLE

# 用户过滤（排除系统用户）
server_audit_excl_users=mysql.session,mysql.sys,debian-sys-maint

# 性能优化
server_audit_syslog_priority=LOG_INFO
EOF
                ;;
            "8.0")
                cat >> "$MYSQL_CNF" << 'EOF'

# ================================
# MySQL 8.0 审计配置 - MariaDB Plugin
# ================================
# 加载审计插件
plugin-load-add=server_audit.so

# 基础配置
server_audit_logging=ON
server_audit_output_type=file
server_audit_file_path=/var/log/mysql/audit.log
server_audit_file_rotate_size=100000000
server_audit_file_rotations=10

# 审计事件类型
server_audit_events=CONNECT,QUERY,TABLE

# 用户过滤（排除系统用户）
server_audit_excl_users=mysql.session,mysql.sys,mysql.infoschema

# 性能优化
server_audit_syslog_priority=LOG_INFO

# MySQL 8.0 特定配置
server_audit_query_log_limit=1024
EOF
                ;;
            *)
                # 默认配置
                cat >> "$MYSQL_CNF" << 'EOF'

# ================================
# MySQL 审计配置 - MariaDB Plugin
# ================================
# 加载审计插件
plugin-load-add=server_audit.so

# 基础配置
server_audit_logging=ON
server_audit_output_type=file
server_audit_file_path=/var/log/mysql/audit.log
server_audit_file_rotate_size=100000000
server_audit_file_rotations=10

# 审计事件类型
server_audit_events=CONNECT,QUERY

# 用户过滤
server_audit_excl_users=

# 性能优化
server_audit_syslog_priority=LOG_INFO
EOF
                ;;
        esac
        
        print_success "MySQL ${MYSQL_VERSION} 审计配置已添加"
    else
        print_warning "MySQL审计配置已存在，跳过"
    fi
}

# 创建审计用户
create_audit_user() {
    print_info "创建MySQL审计用户..."
    
    # 获取MySQL root密码
    read -s -p "请输入MySQL root密码: " MYSQL_ROOT_PASSWORD
    echo
    
    # 审计用户配置
    AUDIT_USER="audit_monitor"
    AUDIT_PASSWORD="AuditMonitor2024!"
    
    # 创建用户和权限
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
-- 创建审计用户
CREATE USER IF NOT EXISTS '${AUDIT_USER}'@'localhost' IDENTIFIED BY '${AUDIT_PASSWORD}';

-- 授予必要权限
GRANT SELECT ON *.* TO '${AUDIT_USER}'@'localhost';
GRANT PROCESS ON *.* TO '${AUDIT_USER}'@'localhost';

-- 创建审计数据库
CREATE DATABASE IF NOT EXISTS mysql_audit;
GRANT ALL PRIVILEGES ON mysql_audit.* TO '${AUDIT_USER}'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 安装审计插件
INSTALL PLUGIN server_audit SONAME 'server_audit.so';

SHOW PLUGINS LIKE 'server_audit';
EOF
    
    if [[ $? -eq 0 ]]; then
        print_success "MySQL审计用户创建成功"
        print_info "用户名: $AUDIT_USER"
        print_info "密码: $AUDIT_PASSWORD"
    else
        print_error "MySQL审计用户创建失败"
        exit 1
    fi
}

# 安装Python依赖
install_python_deps() {
    print_info "安装Python依赖..."
    
    # 创建虚拟环境
    python3 -m venv /opt/mysql-audit/venv
    source /opt/mysql-audit/venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    
    print_success "Python依赖安装完成"
}

# 创建目录结构
create_directories() {
    print_info "创建目录结构..."
    
    # 创建主目录
    mkdir -p /opt/mysql-audit
    mkdir -p /var/log/mysql-audit
    mkdir -p /var/log/mysql
    mkdir -p /etc/mysql-audit
    
    # 设置权限
    chown -R mysql:mysql /var/log/mysql
    chown -R mysql-audit:mysql-audit /var/log/mysql-audit /opt/mysql-audit /etc/mysql-audit || {
        # 如果用户不存在，创建用户
        useradd -r -s /bin/false mysql-audit
        chown -R mysql-audit:mysql-audit /var/log/mysql-audit /opt/mysql-audit /etc/mysql-audit
    }
    
    chmod 755 /opt/mysql-audit
    chmod 750 /var/log/mysql-audit
    
    print_success "目录结构创建完成"
}

# 复制项目文件
copy_project_files() {
    print_info "复制项目文件..."
    
    # 复制源代码
    cp -r src/ /opt/mysql-audit/
    cp -r config/ /etc/mysql-audit/
    cp -r sql/ /opt/mysql-audit/
    
    # 复制配置文件
    cp config/audit_tables.conf /etc/mysql-audit/
    
    # 设置权限
    chown -R mysql-audit:mysql-audit /opt/mysql-audit /etc/mysql-audit
    chmod +x /opt/mysql-audit/src/*.py
    
    print_success "项目文件复制完成"
}

# 创建系统服务
create_systemd_service() {
    print_info "创建系统服务..."
    
    cat > /etc/systemd/system/mysql-audit.service << 'EOF'
[Unit]
Description=MySQL Audit Monitor Service
After=mysql.service
Requires=mysql.service

[Service]
Type=simple
User=mysql-audit
Group=mysql-audit
WorkingDirectory=/opt/mysql-audit
Environment=PYTHONPATH=/opt/mysql-audit/src
ExecStart=/opt/mysql-audit/venv/bin/python /opt/mysql-audit/src/audit_monitor.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mysql-audit

# 安全配置
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=/var/log/mysql-audit /tmp

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    systemctl daemon-reload
    systemctl enable mysql-audit
    
    print_success "系统服务创建完成"
}

# 配置日志轮转
configure_logrotate() {
    print_info "配置日志轮转..."
    
    cat > /etc/logrotate.d/mysql-audit << 'EOF'
/var/log/mysql-audit/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 640 mysql-audit mysql-audit
    postrotate
        /bin/systemctl reload mysql-audit.service > /dev/null 2>&1 || true
    endscript
}

/var/log/mysql/audit.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 640 mysql mysql
    postrotate
        /usr/bin/mysql -e "SET GLOBAL server_audit_file_rotate_now=ON;" > /dev/null 2>&1 || true
    endscript
}
EOF
    
    print_success "日志轮转配置完成"
}

# 重启MySQL服务
restart_mysql() {
    print_info "重启MySQL服务..."
    
    systemctl restart mysql || systemctl restart mysqld
    
    # 等待MySQL启动
    sleep 5
    
    # 检查MySQL状态
    if systemctl is-active --quiet mysql || systemctl is-active --quiet mysqld; then
        print_success "MySQL服务重启成功"
    else
        print_error "MySQL服务重启失败"
        exit 1
    fi
}

# 验证安装
verify_installation() {
    print_info "验证安装..."
    
    # 检查审计插件
    if mysql -e "SHOW PLUGINS LIKE 'server_audit';" | grep -q "server_audit"; then
        print_success "审计插件安装成功"
    else
        print_error "审计插件安装失败"
        return 1
    fi
    
    # 检查审计日志文件
    if [[ -f /var/log/mysql/audit.log ]]; then
        print_success "审计日志文件创建成功"
    else
        print_warning "审计日志文件不存在，将在MySQL重启后创建"
    fi
    
    # 检查Python环境
    if /opt/mysql-audit/venv/bin/python -c "import yaml, loguru, watchdog"; then
        print_success "Python环境验证成功"
    else
        print_error "Python环境验证失败"
        return 1
    fi
    
    print_success "安装验证完成"
}

# 显示安装结果
show_installation_summary() {
    print_info "MySQL审计解决方案安装完成！"
    echo
    print_success "✅ MariaDB审计插件已安装并配置"
    print_success "✅ 审计监控服务已创建"
    print_success "✅ 日志轮转已配置"
    print_success "✅ 系统用户和权限已设置"
    echo
    print_info "📋 配置信息:"
    echo "  审计日志文件: /var/log/mysql/audit.log"
    echo "  监控程序日志: /var/log/mysql-audit/monitor.log"
    echo "  配置文件: /etc/mysql-audit/audit_tables.conf"
    echo "  服务名称: mysql-audit"
    echo
    print_info "🔧 后续步骤:"
    echo "  1. 编辑配置文件指定要监控的表:"
    echo "     vim /etc/mysql-audit/audit_tables.conf"
    echo "  2. 启动审计监控服务:"
    echo "     systemctl start mysql-audit"
    echo "  3. 查看服务状态:"
    echo "     systemctl status mysql-audit"
    echo "  4. 查看实时日志:"
    echo "     tail -f /var/log/mysql-audit/monitor.log"
    echo
    print_warning "⚠️  重要提醒:"
    echo "  - 请妥善保管MySQL审计用户密码"
    echo "  - 定期检查审计日志文件大小"
    echo "  - 根据需要调整监控表配置"
    echo "  - 监控磁盘空间使用情况"
}

# 主函数
main() {
    echo "========================================"
    echo "MySQL 审计解决方案一键安装脚本"
    echo "基于 MariaDB Audit Plugin"
    echo "========================================"
    echo
    
    # 检查权限
    check_root
    
    # 检测系统环境
    detect_os
    
    if ! detect_mysql_version; then
        print_error "请先安装MySQL后再运行此脚本"
        exit 1
    fi
    
    print_info "开始安装MySQL审计解决方案..."
    echo
    
    # 执行安装步骤
    install_dependencies
    create_directories
    download_audit_plugin
    configure_mysql
    restart_mysql
    create_audit_user
    install_python_deps
    copy_project_files
    create_systemd_service
    configure_logrotate
    
    # 验证安装
    if verify_installation; then
        show_installation_summary
    else
        print_error "安装验证失败，请检查错误信息"
        exit 1
    fi
}

# 运行主函数
main "$@"