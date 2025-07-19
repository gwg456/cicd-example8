#!/bin/bash

# 数据库管理脚本
# Database Management Script

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置文件路径
CONFIG_FILE="/root/.userauth_db_config"

# 加载配置
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        source "$CONFIG_FILE"
    else
        echo -e "${RED}配置文件不存在: $CONFIG_FILE${NC}"
        exit 1
    fi
}

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示数据库状态
show_status() {
    log_info "数据库状态信息:"
    echo ""
    
    # PostgreSQL服务状态
    echo "📊 PostgreSQL服务状态:"
    systemctl status postgresql --no-pager -l
    echo ""
    
    # 数据库连接测试
    echo "🔗 数据库连接测试:"
    if sudo -u postgres psql -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
        log_success "数据库连接正常"
    else
        log_error "数据库连接失败"
    fi
    echo ""
    
    # 数据库大小
    echo "💾 数据库大小:"
    sudo -u postgres psql -d "$DB_NAME" -c "
        SELECT 
            pg_size_pretty(pg_database_size('$DB_NAME')) as database_size;
    "
    echo ""
    
    # 表信息
    echo "📋 数据表信息:"
    sudo -u postgres psql -d "$DB_NAME" -c "
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
    "
    echo ""
    
    # 用户统计
    echo "👥 用户统计:"
    sudo -u postgres psql -d "$DB_NAME" -c "
        SELECT 
            COUNT(*) as total_users,
            COUNT(CASE WHEN is_active THEN 1 END) as active_users,
            COUNT(CASE WHEN is_superuser THEN 1 END) as superusers
        FROM users;
    "
}

# 备份数据库
backup_database() {
    local backup_name="$1"
    local backup_dir="/var/backups/userauth"
    
    if [[ -z "$backup_name" ]]; then
        backup_name="manual_$(date +%Y%m%d_%H%M%S)"
    fi
    
    mkdir -p "$backup_dir"
    
    log_info "开始备份数据库..."
    
    local backup_file="$backup_dir/${backup_name}.sql"
    
    if sudo -u postgres pg_dump "$DB_NAME" > "$backup_file"; then
        log_success "数据库备份成功: $backup_file"
        
        # 压缩备份文件
        gzip "$backup_file"
        log_success "备份文件已压缩: ${backup_file}.gz"
        
        # 显示备份文件大小
        local size=$(du -h "${backup_file}.gz" | cut -f1)
        log_info "备份文件大小: $size"
    else
        log_error "数据库备份失败"
        exit 1
    fi
}

# 恢复数据库
restore_database() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]]; then
        log_error "请指定备份文件路径"
        exit 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    log_warning "此操作将覆盖当前数据库内容！"
    read -p "确定要继续吗？(yes/no): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        log_info "操作已取消"
        exit 0
    fi
    
    log_info "开始恢复数据库..."
    
    # 停止API服务
    systemctl stop userauth-api
    
    # 检查文件是否压缩
    if [[ "$backup_file" == *.gz ]]; then
        if zcat "$backup_file" | sudo -u postgres psql "$DB_NAME"; then
            log_success "数据库恢复成功"
        else
            log_error "数据库恢复失败"
            exit 1
        fi
    else
        if sudo -u postgres psql "$DB_NAME" < "$backup_file"; then
            log_success "数据库恢复成功"
        else
            log_error "数据库恢复失败"
            exit 1
        fi
    fi
    
    # 重启API服务
    systemctl start userauth-api
    log_info "API服务已重启"
}

# 列出备份文件
list_backups() {
    local backup_dir="/var/backups/userauth"
    
    if [[ ! -d "$backup_dir" ]]; then
        log_warning "备份目录不存在: $backup_dir"
        return
    fi
    
    log_info "可用备份文件:"
    echo ""
    
    ls -lah "$backup_dir"/*.sql* 2>/dev/null | while read line; do
        echo "  $line"
    done
}

# 清理旧备份
cleanup_backups() {
    local days="$1"
    local backup_dir="/var/backups/userauth"
    
    if [[ -z "$days" ]]; then
        days=7
    fi
    
    log_info "清理 $days 天前的备份文件..."
    
    local count=$(find "$backup_dir" -name "*.sql*" -mtime +$days -type f | wc -l)
    
    if [[ $count -gt 0 ]]; then
        find "$backup_dir" -name "*.sql*" -mtime +$days -type f -delete
        log_success "已清理 $count 个备份文件"
    else
        log_info "没有需要清理的备份文件"
    fi
}

# 重置管理员密码
reset_admin_password() {
    local new_password="$1"
    
    if [[ -z "$new_password" ]]; then
        read -s -p "请输入新密码: " new_password
        echo ""
        read -s -p "确认密码: " confirm_password
        echo ""
        
        if [[ "$new_password" != "$confirm_password" ]]; then
            log_error "密码不匹配"
            exit 1
        fi
    fi
    
    if [[ ${#new_password} -lt 8 ]]; then
        log_error "密码长度至少8位"
        exit 1
    fi
    
    log_info "重置管理员密码..."
    
    # 生成密码哈希
    local password_hash=$(python3 -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd_context.hash('$new_password'))
")
    
    # 更新数据库
    sudo -u postgres psql -d "$DB_NAME" -c "
        UPDATE users 
        SET hashed_password = '$password_hash' 
        WHERE username = 'admin';
    "
    
    log_success "管理员密码已重置"
}

# 创建用户
create_user() {
    local username="$1"
    local email="$2"
    local password="$3"
    local role="$4"
    
    if [[ -z "$username" || -z "$email" || -z "$password" ]]; then
        log_error "用法: $0 create-user <username> <email> <password> [role]"
        exit 1
    fi
    
    if [[ -z "$role" ]]; then
        role="user"
    fi
    
    log_info "创建用户: $username"
    
    # 生成密码哈希
    local password_hash=$(python3 -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd_context.hash('$password'))
")
    
    # 插入用户
    local user_id=$(sudo -u postgres psql -d "$DB_NAME" -t -c "
        INSERT INTO users (username, email, hashed_password, is_active, created_at) 
        VALUES ('$username', '$email', '$password_hash', true, NOW()) 
        RETURNING id;
    " | xargs)
    
    if [[ -n "$user_id" ]]; then
        log_success "用户创建成功，ID: $user_id"
        
        # 分配角色
        local role_id=$(sudo -u postgres psql -d "$DB_NAME" -t -c "
            SELECT id FROM roles WHERE name = '$role';
        " | xargs)
        
        if [[ -n "$role_id" ]]; then
            sudo -u postgres psql -d "$DB_NAME" -c "
                INSERT INTO user_roles (user_id, role_id) VALUES ($user_id, $role_id);
            "
            log_success "角色 '$role' 分配成功"
        else
            log_warning "角色 '$role' 不存在"
        fi
    else
        log_error "用户创建失败"
    fi
}

# 显示帮助信息
show_help() {
    echo "数据库管理脚本"
    echo ""
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  status                          显示数据库状态"
    echo "  backup [name]                   备份数据库"
    echo "  restore <backup_file>           恢复数据库"
    echo "  list-backups                    列出备份文件"
    echo "  cleanup-backups [days]          清理旧备份 (默认7天)"
    echo "  reset-admin-password [password] 重置管理员密码"
    echo "  create-user <user> <email> <pwd> [role] 创建用户"
    echo "  help                            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 status"
    echo "  $0 backup my_backup"
    echo "  $0 restore /var/backups/userauth/backup.sql.gz"
    echo "  $0 cleanup-backups 14"
    echo "  $0 reset-admin-password"
    echo "  $0 create-user john john@example.com password123 manager"
}

# 主函数
main() {
    local command="$1"
    
    case "$command" in
        status)
            load_config
            show_status
            ;;
        backup)
            load_config
            backup_database "$2"
            ;;
        restore)
            load_config
            restore_database "$2"
            ;;
        list-backups)
            list_backups
            ;;
        cleanup-backups)
            cleanup_backups "$2"
            ;;
        reset-admin-password)
            load_config
            reset_admin_password "$2"
            ;;
        create-user)
            load_config
            create_user "$2" "$3" "$4" "$5"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"