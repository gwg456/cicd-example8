#!/bin/bash

# 用户认证系统生产环境部署脚本
# User Auth System Production Deployment Script

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="userauth"
DOMAIN="your-domain.com"
DB_NAME="userauth_prod"
DB_USER="userauth"
DB_PASSWORD=""  # 将在脚本中生成

# 目录配置
PROJECT_DIR="/opt/userauth"
WEB_DIR="/var/www/userauth"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

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

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "请使用root用户运行此脚本"
        exit 1
    fi
}

# 更新系统
update_system() {
    log_info "更新系统软件包..."
    apt update && apt upgrade -y
    log_success "系统更新完成"
}

# 安装必要软件
install_dependencies() {
    log_info "安装必要软件..."
    
    # 基础软件
    apt install -y curl wget git vim ufw fail2ban
    
    # Nginx
    apt install -y nginx
    
    # PostgreSQL
    apt install -y postgresql postgresql-contrib
    
    # Python 3.9+
    apt install -y python3 python3-pip python3-venv python3-dev
    
    # Node.js 18+
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
    
    # SSL工具
    apt install -y certbot python3-certbot-nginx
    
    log_success "依赖软件安装完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    ufw --force enable
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    
    log_success "防火墙配置完成"
}

# 配置PostgreSQL
setup_database() {
    log_info "配置PostgreSQL数据库..."
    
    # 生成随机密码
    DB_PASSWORD=$(openssl rand -base64 32)
    
    # 启动PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
    
    # 创建数据库和用户
    sudo -u postgres psql << EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF

    # 保存数据库配置
    cat > /root/.userauth_db_config << EOF
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
EOF
    
    chmod 600 /root/.userauth_db_config
    
    log_success "数据库配置完成"
    log_info "数据库用户: $DB_USER"
    log_info "数据库密码已保存到: /root/.userauth_db_config"
}

# 克隆项目代码
clone_project() {
    log_info "克隆项目代码..."
    
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR
    
    # 这里假设代码已经在某个git仓库中
    # git clone https://github.com/yourusername/userauth.git .
    
    # 如果没有git仓库，需要手动上传代码到服务器
    log_warning "请确保项目代码已上传到 $PROJECT_DIR"
    
    log_success "项目代码准备完成"
}

# 部署后端
deploy_backend() {
    log_info "部署后端应用..."
    
    cd $BACKEND_DIR
    
    # 创建Python虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 安装依赖
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 生成JWT密钥
    JWT_SECRET=$(openssl rand -hex 32)
    
    # 创建生产环境配置
    cat > .env << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
SECRET_KEY=$JWT_SECRET
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
BCRYPT_ROUNDS=12
APP_NAME=User Auth API
DEBUG=false
ALLOWED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
LOG_LEVEL=INFO
EOF

    # 初始化数据库
    python scripts/init_db.py
    
    log_success "后端部署完成"
}

# 部署前端
deploy_frontend() {
    log_info "部署前端应用..."
    
    cd $FRONTEND_DIR
    
    # 安装依赖
    npm install
    
    # 创建生产环境配置
    cat > .env.production << EOF
VITE_API_BASE_URL=https://$DOMAIN
VITE_APP_TITLE=用户认证系统
VITE_APP_VERSION=1.0.0
EOF

    # 构建生产版本
    npm run build
    
    # 部署到Web目录
    mkdir -p $WEB_DIR
    cp -r dist/* $WEB_DIR/
    
    # 设置权限
    chown -R www-data:www-data $WEB_DIR
    chmod -R 755 $WEB_DIR
    
    log_success "前端部署完成"
}

# 配置Nginx
setup_nginx() {
    log_info "配置Nginx..."
    
    # 复制配置文件
    cp deployment/nginx/userauth.conf /etc/nginx/sites-available/
    
    # 修改域名
    sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/userauth.conf
    
    # 启用站点
    ln -sf /etc/nginx/sites-available/userauth.conf /etc/nginx/sites-enabled/
    
    # 删除默认站点
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试配置
    nginx -t
    
    # 重载Nginx
    systemctl reload nginx
    systemctl enable nginx
    
    log_success "Nginx配置完成"
}

# 配置SSL证书
setup_ssl() {
    log_info "配置SSL证书..."
    
    # 临时停止Nginx
    systemctl stop nginx
    
    # 获取Let's Encrypt证书
    certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email admin@$DOMAIN --agree-tos --non-interactive
    
    # 启动Nginx
    systemctl start nginx
    
    # 设置自动续期
    crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx"; } | crontab -
    
    log_success "SSL证书配置完成"
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."
    
    cat > /etc/systemd/system/userauth-api.service << EOF
[Unit]
Description=User Auth API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$BACKEND_DIR
Environment=PATH=$BACKEND_DIR/venv/bin
ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=userauth-api

[Install]
WantedBy=multi-user.target
EOF

    # 重载systemd
    systemctl daemon-reload
    
    # 启动服务
    systemctl start userauth-api
    systemctl enable userauth-api
    
    log_success "systemd服务创建完成"
}

# 配置日志轮转
setup_log_rotation() {
    log_info "配置日志轮转..."
    
    cat > /etc/logrotate.d/userauth << EOF
/var/log/nginx/userauth_*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data adm
    postrotate
        systemctl reload nginx
    endscript
}
EOF

    log_success "日志轮转配置完成"
}

# 设置监控和健康检查
setup_monitoring() {
    log_info "设置基础监控..."
    
    # 创建健康检查脚本
    cat > /opt/userauth/health_check.sh << 'EOF'
#!/bin/bash

# 检查API健康状态
api_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$api_status" != "200" ]; then
    echo "API健康检查失败: $api_status"
    systemctl restart userauth-api
    exit 1
fi

# 检查数据库连接
if ! sudo -u postgres psql -d userauth_prod -c "SELECT 1;" > /dev/null 2>&1; then
    echo "数据库连接失败"
    exit 1
fi

echo "所有服务正常"
EOF

    chmod +x /opt/userauth/health_check.sh
    
    # 添加cron任务
    crontab -l 2>/dev/null | { cat; echo "*/5 * * * * /opt/userauth/health_check.sh"; } | crontab -
    
    log_success "监控配置完成"
}

# 创建备份脚本
create_backup_script() {
    log_info "创建备份脚本..."
    
    cat > /opt/userauth/backup.sh << EOF
#!/bin/bash

BACKUP_DIR="/var/backups/userauth"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# 备份数据库
sudo -u postgres pg_dump $DB_NAME > \$BACKUP_DIR/database_\$DATE.sql

# 备份配置文件
tar -czf \$BACKUP_DIR/config_\$DATE.tar.gz $BACKEND_DIR/.env /etc/nginx/sites-available/userauth.conf

# 清理7天前的备份
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: \$DATE"
EOF

    chmod +x /opt/userauth/backup.sh
    
    # 添加每日备份cron任务
    crontab -l 2>/dev/null | { cat; echo "0 2 * * * /opt/userauth/backup.sh"; } | crontab -
    
    log_success "备份脚本创建完成"
}

# 显示部署信息
show_deployment_info() {
    log_success "🎉 部署完成！"
    echo ""
    echo "📋 部署信息:"
    echo "  🌐 网站地址: https://$DOMAIN"
    echo "  📚 API文档: https://$DOMAIN/docs"
    echo "  🗄️  数据库: $DB_NAME"
    echo "  👤 数据库用户: $DB_USER"
    echo ""
    echo "📁 重要目录:"
    echo "  📦 项目目录: $PROJECT_DIR"
    echo "  🌐 Web目录: $WEB_DIR"
    echo "  💾 备份目录: /var/backups/userauth"
    echo ""
    echo "🛠️  管理命令:"
    echo "  🔄 重启API: systemctl restart userauth-api"
    echo "  📊 查看API状态: systemctl status userauth-api"
    echo "  📄 查看API日志: journalctl -u userauth-api -f"
    echo "  🔄 重载Nginx: systemctl reload nginx"
    echo "  💾 手动备份: /opt/userauth/backup.sh"
    echo ""
    echo "🔐 默认账户:"
    echo "  👤 超级管理员 - 用户名: admin, 密码: admin123"
    echo ""
    log_warning "请立即修改默认管理员密码！"
    echo ""
    echo "📖 详细配置信息请查看: /root/.userauth_db_config"
}

# 主函数
main() {
    log_info "开始部署用户认证系统..."
    
    # 检查域名参数
    if [ "$1" != "" ]; then
        DOMAIN="$1"
        log_info "使用域名: $DOMAIN"
    else
        log_warning "未指定域名，使用默认域名: $DOMAIN"
        log_warning "使用方法: $0 <your-domain.com>"
    fi
    
    # 执行部署步骤
    check_root
    update_system
    install_dependencies
    setup_firewall
    setup_database
    clone_project
    deploy_backend
    deploy_frontend
    setup_nginx
    setup_ssl
    create_systemd_service
    setup_log_rotation
    setup_monitoring
    create_backup_script
    
    show_deployment_info
}

# 运行主函数
main "$@"