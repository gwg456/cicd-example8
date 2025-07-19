#!/bin/bash
# MySQL 数据库变更监控系统 - MySQL配置脚本
# 基于 Binary Log 的完整配置

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
        exit 1
    fi
}

# 检测MySQL版本
detect_mysql_version() {
    if command -v mysql >/dev/null 2>&1; then
        MYSQL_VERSION=$(mysql --version | awk '{print $5}' | awk -F, '{print $1}')
        print_info "检测到MySQL版本: $MYSQL_VERSION"
        return 0
    else
        print_error "未检测到MySQL，请先安装MySQL"
        exit 1
    fi
}

# 配置Binary Log
configure_binlog() {
    print_info "配置MySQL Binary Log..."
    
    # 查找MySQL配置文件
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
    
    print_info "使用配置文件: $MYSQL_CNF"
    
    # 备份原配置文件
    cp "$MYSQL_CNF" "${MYSQL_CNF}.backup.$(date +%Y%m%d_%H%M%S)"
    print_success "已备份原配置文件"
    
    # 检查并添加Binary Log配置
    if ! grep -q "log-bin" "$MYSQL_CNF"; then
        print_info "添加Binary Log配置..."
        
        cat >> "$MYSQL_CNF" << 'EOF'

# ================================
# Binary Log 配置 - 用于变更监控
# ================================
# 启用Binary Log
log-bin = mysql-bin

# Binary Log格式：ROW格式记录每行的变更
binlog_format = ROW

# Binary Log过期时间（天）
expire_logs_days = 7

# 最大Binary Log文件大小（1GB）
max_binlog_size = 1073741824

# 事务缓存大小
binlog_cache_size = 32768

# 同步策略：每次事务提交都同步到磁盘（安全性最高）
sync_binlog = 1

# Server ID（每个MySQL实例需要唯一）
server-id = 1

# GTID模式（可选，便于复制管理）
gtid_mode = ON
enforce_gtid_consistency = ON

# 记录更详细的日志信息
log_slave_updates = 1
EOF
        
        print_success "已添加Binary Log配置"
    else
        print_warning "Binary Log配置已存在，跳过"
    fi
}

# 创建监控用户
create_monitor_user() {
    print_info "创建监控用户..."
    
    # 获取MySQL root密码
    read -s -p "请输入MySQL root密码: " MYSQL_ROOT_PASSWORD
    echo
    
    # 监控用户配置
    MONITOR_USER="change_monitor"
    MONITOR_PASSWORD="ChangeMonitor2024!"
    
    # 连接MySQL并创建用户
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
-- 创建监控用户
CREATE USER IF NOT EXISTS '${MONITOR_USER}'@'localhost' IDENTIFIED BY '${MONITOR_PASSWORD}';
CREATE USER IF NOT EXISTS '${MONITOR_USER}'@'%' IDENTIFIED BY '${MONITOR_PASSWORD}';

-- 授予必要权限
-- REPLICATION SLAVE: 读取Binary Log
-- REPLICATION CLIENT: 获取binlog位置信息
-- SELECT: 查询权限（用于获取表结构等）
GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO '${MONITOR_USER}'@'localhost';
GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO '${MONITOR_USER}'@'%';
GRANT SELECT ON *.* TO '${MONITOR_USER}'@'localhost';
GRANT SELECT ON *.* TO '${MONITOR_USER}'@'%';

-- 如果使用MySQL存储变更记录，需要额外权限
CREATE DATABASE IF NOT EXISTS change_monitor;
GRANT ALL PRIVILEGES ON change_monitor.* TO '${MONITOR_USER}'@'localhost';
GRANT ALL PRIVILEGES ON change_monitor.* TO '${MONITOR_USER}'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示用户权限
SHOW GRANTS FOR '${MONITOR_USER}'@'localhost';
EOF
    
    if [[ $? -eq 0 ]]; then
        print_success "监控用户创建成功"
        print_info "用户名: $MONITOR_USER"
        print_info "密码: $MONITOR_PASSWORD"
        print_warning "请妥善保管用户密码，并更新监控系统配置文件"
    else
        print_error "监控用户创建失败"
        exit 1
    fi
}

# 测试Binary Log状态
test_binlog_status() {
    print_info "检查Binary Log状态..."
    
    # 获取监控用户密码
    read -s -p "请输入监控用户(${MONITOR_USER:-change_monitor})密码: " MONITOR_PASSWORD
    echo
    
    # 测试连接和权限
    mysql -u "${MONITOR_USER:-change_monitor}" -p"$MONITOR_PASSWORD" << 'EOF'
-- 检查Binary Log状态
SHOW VARIABLES LIKE 'log_bin';
SHOW VARIABLES LIKE 'binlog_format';
SHOW VARIABLES LIKE 'server_id';

-- 检查当前Binary Log文件
SHOW MASTER STATUS;

-- 检查Binary Log文件列表
SHOW BINARY LOGS;

-- 检查用户权限
SHOW GRANTS FOR CURRENT_USER();
EOF
    
    if [[ $? -eq 0 ]]; then
        print_success "Binary Log配置验证成功"
    else
        print_error "Binary Log配置验证失败"
    fi
}

# 重启MySQL服务
restart_mysql() {
    print_info "重启MySQL服务以应用配置..."
    
    # 检测MySQL服务管理方式
    if systemctl is-active --quiet mysql; then
        systemctl restart mysql
        print_success "MySQL服务重启成功 (systemctl)"
    elif systemctl is-active --quiet mysqld; then
        systemctl restart mysqld
        print_success "MySQL服务重启成功 (systemctl mysqld)"
    elif service mysql status >/dev/null 2>&1; then
        service mysql restart
        print_success "MySQL服务重启成功 (service)"
    else
        print_warning "无法自动重启MySQL服务，请手动重启"
        print_info "可尝试以下命令之一:"
        print_info "  systemctl restart mysql"
        print_info "  systemctl restart mysqld"
        print_info "  service mysql restart"
        return 1
    fi
    
    # 等待MySQL启动
    print_info "等待MySQL服务启动..."
    sleep 5
    
    # 检查MySQL是否正常运行
    if mysqladmin ping >/dev/null 2>&1; then
        print_success "MySQL服务运行正常"
    else
        print_error "MySQL服务启动失败"
        return 1
    fi
}

# 创建配置更新脚本
create_config_updater() {
    print_info "创建配置文件更新脚本..."
    
    cat > /usr/local/bin/update_mysql_monitor_config.sh << 'EOF'
#!/bin/bash
# MySQL监控配置更新脚本

CONFIG_FILE="../config/monitor.conf"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 更新数据库连接配置
read -p "数据库主机 [localhost]: " DB_HOST
read -p "数据库端口 [3306]: " DB_PORT
read -p "监控用户名 [change_monitor]: " DB_USER
read -s -p "监控用户密码: " DB_PASSWORD
echo

# 使用默认值
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-3306}
DB_USER=${DB_USER:-change_monitor}

# 更新配置文件
sed -i "s/host: .*/host: $DB_HOST/" "$CONFIG_FILE"
sed -i "s/port: .*/port: $DB_PORT/" "$CONFIG_FILE"
sed -i "s/user: .*/user: $DB_USER/" "$CONFIG_FILE"
sed -i "s/password: .*/password: \"$DB_PASSWORD\"/" "$CONFIG_FILE"

echo "配置文件已更新"
EOF
    
    chmod +x /usr/local/bin/update_mysql_monitor_config.sh
    print_success "配置更新脚本已创建: /usr/local/bin/update_mysql_monitor_config.sh"
}

# 显示配置信息
show_configuration() {
    print_info "MySQL Binary Log监控配置完成！"
    echo
    print_success "✅ Binary Log已启用并配置"
    print_success "✅ 监控用户已创建"
    print_success "✅ 必要权限已授予"
    echo
    print_info "📋 配置信息:"
    echo "  监控用户: ${MONITOR_USER:-change_monitor}"
    echo "  数据库权限: REPLICATION SLAVE, REPLICATION CLIENT, SELECT"
    echo "  Binary Log格式: ROW"
    echo "  日志保留期: 7天"
    echo
    print_info "🔧 后续步骤:"
    echo "  1. 更新监控系统配置文件 config/monitor.conf"
    echo "  2. 配置要监控的数据库和表"
    echo "  3. 启动监控系统: python monitor.py"
    echo
    print_info "🛠️  配置更新:"
    echo "  运行: /usr/local/bin/update_mysql_monitor_config.sh"
    echo
    print_warning "⚠️  重要提醒:"
    echo "  - Binary Log会增加磁盘使用量"
    echo "  - 定期清理过期的Binary Log文件"
    echo "  - 监控磁盘空间使用情况"
    echo "  - 保护监控用户密码安全"
}

# 主函数
main() {
    echo "================================"
    echo "MySQL 变更监控系统配置脚本"
    echo "基于 Binary Log 的完整配置"
    echo "================================"
    echo
    
    # 检查权限
    check_root
    
    # 检测MySQL
    detect_mysql_version
    
    # 执行配置步骤
    echo
    print_info "开始配置MySQL Binary Log监控..."
    
    # 1. 配置Binary Log
    configure_binlog
    
    # 2. 重启MySQL
    if restart_mysql; then
        # 3. 创建监控用户
        create_monitor_user
        
        # 4. 测试配置
        test_binlog_status
        
        # 5. 创建配置工具
        create_config_updater
        
        # 6. 显示配置信息
        show_configuration
    else
        print_error "MySQL重启失败，请检查配置并手动重启"
        exit 1
    fi
}

# 运行主函数
main "$@"