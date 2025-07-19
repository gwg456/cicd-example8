#!/bin/bash
# MySQL 审计系统配置脚本
# 用于配置MySQL以支持完整的审计功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}MySQL 审计系统配置脚本${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要root权限运行"
        echo "请使用: sudo $0"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    print_info "检测到操作系统: $OS $VER"
}

# 检查MySQL版本
check_mysql_version() {
    if command -v mysql >/dev/null 2>&1; then
        MYSQL_VERSION=$(mysql --version | awk '{print $3}' | cut -d',' -f1)
        print_info "检测到MySQL版本: $MYSQL_VERSION"
        
        # 检查版本兼容性
        if [[ $MYSQL_VERSION < "5.7" ]]; then
            print_warning "MySQL版本过低，建议升级至5.7或更高版本"
        fi
    else
        print_error "未检测到MySQL，请先安装MySQL"
        exit 1
    fi
}

# 获取MySQL配置文件路径
get_mysql_config() {
    # 常见的MySQL配置文件路径
    CONFIG_PATHS=(
        "/etc/mysql/mysql.conf.d/mysqld.cnf"
        "/etc/mysql/my.cnf"
        "/etc/my.cnf"
        "/usr/local/mysql/my.cnf"
        "/opt/mysql/my.cnf"
    )
    
    for path in "${CONFIG_PATHS[@]}"; do
        if [ -f "$path" ]; then
            MYSQL_CONFIG="$path"
            print_info "找到MySQL配置文件: $MYSQL_CONFIG"
            return 0
        fi
    done
    
    print_error "未找到MySQL配置文件"
    return 1
}

# 备份MySQL配置文件
backup_mysql_config() {
    local backup_file="${MYSQL_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$MYSQL_CONFIG" "$backup_file"
    print_success "已备份MySQL配置文件到: $backup_file"
}

# 配置MySQL日志
configure_mysql_logging() {
    print_info "配置MySQL日志设置..."
    
    # 创建日志目录
    local log_dir="/var/log/mysql"
    if [ ! -d "$log_dir" ]; then
        mkdir -p "$log_dir"
        chown mysql:mysql "$log_dir"
        chmod 750 "$log_dir"
        print_success "创建日志目录: $log_dir"
    fi
    
    # 读取当前配置
    local temp_config=$(mktemp)
    cp "$MYSQL_CONFIG" "$temp_config"
    
    # 添加或更新审计相关配置
    cat >> "$temp_config" << 'EOF'

# ==============================================
# MySQL 审计系统配置
# 自动生成，请勿手动修改此部分
# ==============================================

[mysqld]
# General Log 配置
general_log = 1
general_log_file = /var/log/mysql/general.log

# Binary Log 配置
log-bin = /var/log/mysql/mysql-bin
binlog_format = ROW
binlog_row_image = FULL
binlog_expire_logs_seconds = 604800
max_binlog_size = 100M

# Slow Query Log 配置
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
log_queries_not_using_indexes = 1
log_slow_admin_statements = 1
log_slow_slave_statements = 1

# Error Log 配置
log_error = /var/log/mysql/error.log
log_error_verbosity = 3

# Performance Schema 配置
performance_schema = 1
performance_schema_max_thread_instances = 1000
performance_schema_max_thread_classes = 100

# Performance Schema 事件收集器
performance_schema_consumer_events_statements_current = ON
performance_schema_consumer_events_statements_history = ON
performance_schema_consumer_events_statements_history_long = ON
performance_schema_consumer_events_waits_current = ON
performance_schema_consumer_events_waits_history = ON
performance_schema_consumer_events_waits_history_long = ON

# Performance Schema 工具
performance_schema_instrument = 'statement/%=ON'
performance_schema_instrument = 'wait/%=ON'

# 连接和权限日志
log_warnings = 2

# 审计相关安全设置
secure_file_priv = '/var/lib/mysql-files/'
local_infile = 0

# 日志刷新设置
sync_binlog = 1
innodb_flush_log_at_trx_commit = 1

# ==============================================
# 审计系统配置结束
# ==============================================
EOF

    # 应用配置
    mv "$temp_config" "$MYSQL_CONFIG"
    print_success "已更新MySQL配置文件"
}

# 创建审计用户
create_audit_user() {
    print_info "创建MySQL审计用户..."
    
    read -p "请输入MySQL root密码: " -s mysql_root_password
    echo ""
    
    # 测试连接
    if ! mysql -u root -p"$mysql_root_password" -e "SELECT 1;" >/dev/null 2>&1; then
        print_error "MySQL连接失败，请检查密码"
        return 1
    fi
    
    # 生成随机密码
    local audit_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # 创建审计用户和数据库
    mysql -u root -p"$mysql_root_password" << EOF
-- 创建审计数据库
CREATE DATABASE IF NOT EXISTS mysql_audit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建审计用户
CREATE USER IF NOT EXISTS 'mysql_audit_user'@'localhost' IDENTIFIED BY '$audit_password';

-- 授予必要权限
GRANT SELECT ON mysql.* TO 'mysql_audit_user'@'localhost';
GRANT SELECT ON information_schema.* TO 'mysql_audit_user'@'localhost';
GRANT SELECT ON performance_schema.* TO 'mysql_audit_user'@'localhost';
GRANT ALL PRIVILEGES ON mysql_audit.* TO 'mysql_audit_user'@'localhost';

-- 授予PROCESS权限以查看进程列表
GRANT PROCESS ON *.* TO 'mysql_audit_user'@'localhost';

-- 授予REPLICATION CLIENT权限以读取binlog
GRANT REPLICATION CLIENT ON *.* TO 'mysql_audit_user'@'localhost';

-- 授予SELECT权限以读取用户表
GRANT SELECT ON mysql.user TO 'mysql_audit_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 创建审计表结构
USE mysql_audit;

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME(6) NOT NULL,
    thread_id BIGINT,
    connection_id BIGINT,
    user_name VARCHAR(255),
    host VARCHAR(255),
    database_name VARCHAR(255),
    command VARCHAR(50),
    sql_type VARCHAR(50),
    sql_statement TEXT,
    table_names JSON,
    execution_time DECIMAL(10,3),
    rows_affected BIGINT,
    status VARCHAR(20),
    error_code INT,
    error_message TEXT,
    source VARCHAR(50),
    risk_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_user (user_name),
    INDEX idx_database (database_name),
    INDEX idx_command (command),
    INDEX idx_status (status),
    INDEX idx_risk_level (risk_level)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS security_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME(6) NOT NULL,
    event_type VARCHAR(100),
    severity VARCHAR(20),
    user_name VARCHAR(255),
    host VARCHAR(255),
    database_name VARCHAR(255),
    description TEXT,
    details JSON,
    risk_score INT,
    status VARCHAR(20) DEFAULT 'NEW',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_event_type (event_type),
    INDEX idx_severity (severity),
    INDEX idx_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50),
    conditions JSON,
    actions JSON,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_name (name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_key DATE NOT NULL,
    total_queries BIGINT DEFAULT 0,
    select_queries BIGINT DEFAULT 0,
    insert_queries BIGINT DEFAULT 0,
    update_queries BIGINT DEFAULT 0,
    delete_queries BIGINT DEFAULT 0,
    ddl_queries BIGINT DEFAULT 0,
    failed_queries BIGINT DEFAULT 0,
    suspicious_queries BIGINT DEFAULT 0,
    unique_users INT DEFAULT 0,
    unique_hosts INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_date (date_key)
) ENGINE=InnoDB;
EOF

    if [ $? -eq 0 ]; then
        print_success "审计用户和数据库创建成功"
        
        # 保存用户信息到配置文件
        local config_dir="/etc/mysql-audit"
        mkdir -p "$config_dir"
        
        cat > "$config_dir/database.conf" << EOF
# MySQL审计系统数据库配置
[database]
host = localhost
port = 3306
user = mysql_audit_user
password = $audit_password
database = mysql_audit
charset = utf8mb4

[mysql]
host = localhost
port = 3306
user = mysql_audit_user
password = $audit_password
database = mysql
charset = utf8mb4
EOF

        chmod 600 "$config_dir/database.conf"
        print_success "数据库配置已保存到: $config_dir/database.conf"
        print_warning "请妥善保管审计用户密码: $audit_password"
    else
        print_error "创建审计用户失败"
        return 1
    fi
}

# 配置文件权限
configure_permissions() {
    print_info "配置文件权限..."
    
    # 确保MySQL用户可以写入日志文件
    touch /var/log/mysql/general.log
    touch /var/log/mysql/slow.log
    touch /var/log/mysql/error.log
    
    chown mysql:mysql /var/log/mysql/*.log
    chmod 640 /var/log/mysql/*.log
    
    # 创建安全文件目录
    mkdir -p /var/lib/mysql-files
    chown mysql:mysql /var/lib/mysql-files
    chmod 750 /var/lib/mysql-files
    
    print_success "文件权限配置完成"
}

# 配置日志轮转
configure_logrotate() {
    print_info "配置日志轮转..."
    
    cat > /etc/logrotate.d/mysql-audit << 'EOF'
/var/log/mysql/general.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 mysql mysql
    postrotate
        if test -x /usr/bin/mysqladmin && \
           /usr/bin/mysqladmin ping &>/dev/null
        then
           /usr/bin/mysqladmin flush-logs
        fi
    endscript
}

/var/log/mysql/slow.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 mysql mysql
    postrotate
        if test -x /usr/bin/mysqladmin && \
           /usr/bin/mysqladmin ping &>/dev/null
        then
           /usr/bin/mysqladmin flush-logs
        fi
    endscript
}

/var/log/mysql/error.log {
    weekly
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 640 mysql mysql
    postrotate
        if test -x /usr/bin/mysqladmin && \
           /usr/bin/mysqladmin ping &>/dev/null
        then
           /usr/bin/mysqladmin flush-logs
        fi
    endscript
}
EOF

    print_success "日志轮转配置完成"
}

# 重启MySQL服务
restart_mysql() {
    print_info "重启MySQL服务以应用配置..."
    
    # 检测MySQL服务名称
    local service_name=""
    if systemctl list-units --type=service | grep -q mysql; then
        service_name="mysql"
    elif systemctl list-units --type=service | grep -q mysqld; then
        service_name="mysqld"
    else
        print_error "无法检测MySQL服务名称"
        return 1
    fi
    
    # 重启服务
    if systemctl restart "$service_name"; then
        print_success "MySQL服务重启成功"
        
        # 等待服务启动
        sleep 5
        
        # 验证服务状态
        if systemctl is-active --quiet "$service_name"; then
            print_success "MySQL服务运行正常"
        else
            print_error "MySQL服务启动失败"
            systemctl status "$service_name"
            return 1
        fi
    else
        print_error "MySQL服务重启失败"
        return 1
    fi
}

# 验证配置
verify_configuration() {
    print_info "验证配置..."
    
    # 检查日志文件
    local log_files=(
        "/var/log/mysql/general.log"
        "/var/log/mysql/slow.log"
        "/var/log/mysql/error.log"
    )
    
    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            print_success "日志文件存在: $log_file"
        else
            print_warning "日志文件不存在: $log_file"
        fi
    done
    
    # 检查MySQL变量
    if [ -f "/etc/mysql-audit/database.conf" ]; then
        local audit_user=$(grep "user = " /etc/mysql-audit/database.conf | cut -d' ' -f3)
        local audit_password=$(grep "password = " /etc/mysql-audit/database.conf | cut -d' ' -f3)
        
        if mysql -u "$audit_user" -p"$audit_password" -e "SHOW VARIABLES LIKE 'general_log';" >/dev/null 2>&1; then
            print_success "审计用户连接正常"
            
            # 检查关键变量
            local variables=(
                "general_log"
                "slow_query_log"
                "log_bin"
                "performance_schema"
            )
            
            for var in "${variables[@]}"; do
                local value=$(mysql -u "$audit_user" -p"$audit_password" -s -N -e "SHOW VARIABLES LIKE '$var';" | awk '{print $2}')
                if [ "$value" = "ON" ] || [ "$value" = "1" ]; then
                    print_success "$var = $value"
                else
                    print_warning "$var = $value"
                fi
            done
        else
            print_error "审计用户连接失败"
        fi
    fi
}

# 显示配置摘要
show_summary() {
    print_info "配置摘要:"
    echo ""
    echo "✅ MySQL配置文件: $MYSQL_CONFIG"
    echo "✅ 日志目录: /var/log/mysql/"
    echo "✅ 审计数据库: mysql_audit"
    echo "✅ 配置文件: /etc/mysql-audit/database.conf"
    echo ""
    echo "📋 启用的功能:"
    echo "  - General Log (所有SQL语句)"
    echo "  - Binary Log (数据变更)"
    echo "  - Slow Query Log (慢查询)"
    echo "  - Performance Schema (性能监控)"
    echo "  - Error Log (错误日志)"
    echo ""
    echo "🔧 下一步:"
    echo "  1. 安装Python审计系统: pip install -r requirements.txt"
    echo "  2. 配置审计规则: vim config/audit.conf"
    echo "  3. 启动审计服务: ./scripts/start_audit.sh"
    echo ""
    print_success "MySQL审计系统配置完成！"
}

# 主函数
main() {
    print_header
    
    check_root
    detect_os
    check_mysql_version
    
    if ! get_mysql_config; then
        exit 1
    fi
    
    print_info "开始配置MySQL审计系统..."
    echo ""
    
    backup_mysql_config
    configure_mysql_logging
    create_audit_user
    configure_permissions
    configure_logrotate
    restart_mysql
    verify_configuration
    
    echo ""
    show_summary
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi