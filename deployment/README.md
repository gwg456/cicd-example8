# 用户认证系统 - 生产环境部署指南

## 🚀 快速部署

### 一键部署脚本
```bash
# 1. 下载部署脚本
wget https://raw.githubusercontent.com/your-repo/userauth/main/deployment/scripts/deploy.sh

# 2. 赋予执行权限
chmod +x deploy.sh

# 3. 运行部署（替换为您的域名）
sudo ./deploy.sh your-domain.com
```

## 📋 系统要求

### 服务器配置
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **内存**: 最低 2GB，推荐 4GB+
- **存储**: 最低 20GB，推荐 50GB+
- **CPU**: 最低 2 核，推荐 4 核+
- **网络**: 稳定的外网连接

### 域名和SSL
- 已备案的域名（如果在中国大陆）
- DNS解析指向服务器IP
- 可选：SSL证书（脚本会自动申请Let's Encrypt证书）

## 🛠️ 手动部署步骤

### 1. 准备服务器环境
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础软件
sudo apt install -y curl wget git vim ufw fail2ban

# 配置防火墙
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
```

### 2. 安装数据库 (PostgreSQL)
```bash
# 安装PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库
sudo -u postgres psql << 'EOF'
CREATE USER userauth WITH PASSWORD 'your_secure_password';
CREATE DATABASE userauth_prod OWNER userauth;
GRANT ALL PRIVILEGES ON DATABASE userauth_prod TO userauth;
\q
EOF
```

### 3. 安装后端依赖
```bash
# 安装Python 3.9+
sudo apt install -y python3 python3-pip python3-venv python3-dev

# 创建项目目录
sudo mkdir -p /opt/userauth/backend
cd /opt/userauth/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 配置后端
```bash
# 创建环境配置文件
cat > .env << 'EOF'
DATABASE_URL=postgresql://userauth:your_secure_password@localhost:5432/userauth_prod
SECRET_KEY=your-very-secure-secret-key-32-chars-minimum
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
BCRYPT_ROUNDS=12
APP_NAME=User Auth API
DEBUG=false
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
LOG_LEVEL=INFO
EOF

# 初始化数据库
python scripts/init_db.py
```

### 5. 安装前端依赖
```bash
# 安装Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 前端项目目录
cd /opt/userauth/frontend

# 安装依赖
npm install

# 配置生产环境
cat > .env.production.local << 'EOF'
VITE_API_BASE_URL=
VITE_APP_TITLE=用户认证系统
VITE_APP_VERSION=1.0.0
VITE_DEBUG=false
EOF

# 构建前端
npm run build
```

### 6. 部署前端文件
```bash
# 创建Web目录
sudo mkdir -p /var/www/userauth

# 复制文件
sudo cp -r dist/* /var/www/userauth/

# 设置权限
sudo chown -R www-data:www-data /var/www/userauth
sudo chmod -R 755 /var/www/userauth
```

### 7. 安装和配置Nginx
```bash
# 安装Nginx
sudo apt install -y nginx

# 复制配置文件
sudo cp deployment/nginx/userauth.conf /etc/nginx/sites-available/

# 修改域名
sudo sed -i 's/your-domain.com/实际域名/g' /etc/nginx/sites-available/userauth.conf

# 启用站点
sudo ln -sf /etc/nginx/sites-available/userauth.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 启动Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 8. 配置SSL证书
```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书（替换为您的域名和邮箱）
sudo certbot --nginx -d your-domain.com -d www.your-domain.com --email admin@your-domain.com --agree-tos --non-interactive

# 设置自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx" | sudo crontab -
```

### 9. 创建systemd服务
```bash
# 创建后端API服务
sudo tee /etc/systemd/system/userauth-api.service << 'EOF'
[Unit]
Description=User Auth API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/userauth/backend
Environment=PATH=/opt/userauth/backend/venv/bin
ExecStart=/opt/userauth/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=userauth-api

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl start userauth-api
sudo systemctl enable userauth-api
```

## 🔧 配置说明

### 数据库配置
- **数据库名**: `userauth_prod`
- **用户**: `userauth`
- **密码**: 请使用强密码并安全保存
- **连接**: 仅限本地连接，提高安全性

### 前端API配置
- **同域名部署**: `VITE_API_BASE_URL=` (留空)
- **不同域名**: `VITE_API_BASE_URL=https://api.yourdomain.com`
- **开发环境**: `VITE_API_BASE_URL=http://localhost:8000`

### Nginx配置要点
- 静态文件缓存 1 年
- API请求代理到后端
- 安全头配置
- 请求频率限制
- Gzip压缩

## 🔐 安全配置

### 1. JWT密钥
```bash
# 生成安全的JWT密钥
openssl rand -hex 32
```

### 2. 数据库密码
```bash
# 生成安全的数据库密码
openssl rand -base64 32
```

### 3. 防火墙配置
```bash
# 只开放必要端口
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 4. Fail2ban配置
```bash
# 安装Fail2ban防止暴力破解
sudo apt install -y fail2ban

# 创建配置文件
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF

sudo systemctl restart fail2ban
```

## 📊 监控和维护

### 1. 系统监控
```bash
# 查看服务状态
sudo systemctl status userauth-api
sudo systemctl status nginx
sudo systemctl status postgresql

# 查看API日志
sudo journalctl -u userauth-api -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/userauth_access.log
sudo tail -f /var/log/nginx/userauth_error.log
```

### 2. 数据库管理
```bash
# 使用数据库管理脚本
cd /opt/userauth
chmod +x deployment/scripts/db_manage.sh

# 查看数据库状态
./deployment/scripts/db_manage.sh status

# 备份数据库
./deployment/scripts/db_manage.sh backup

# 重置管理员密码
./deployment/scripts/db_manage.sh reset-admin-password
```

### 3. 自动备份
```bash
# 添加自动备份cron任务
sudo crontab -e

# 添加以下行（每天凌晨2点备份）
0 2 * * * /opt/userauth/deployment/scripts/db_manage.sh backup
```

## 🔄 更新和升级

### 1. 更新后端
```bash
cd /opt/userauth/backend
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart userauth-api
```

### 2. 更新前端
```bash
cd /opt/userauth/frontend
git pull origin main
npm install
npm run build
sudo cp -r dist/* /var/www/userauth/
```

### 3. 数据库迁移
```bash
cd /opt/userauth/backend
source venv/bin/activate
alembic upgrade head
```

## 🐛 故障排除

### 常见问题

#### 1. API服务无法启动
```bash
# 检查日志
sudo journalctl -u userauth-api -n 50

# 检查端口占用
sudo netstat -tlnp | grep :8000

# 检查数据库连接
sudo -u postgres psql -d userauth_prod -c "SELECT 1;"
```

#### 2. 前端无法访问API
```bash
# 检查Nginx配置
sudo nginx -t

# 检查代理配置
curl -I http://localhost:8000/health

# 检查域名解析
nslookup your-domain.com
```

#### 3. SSL证书问题
```bash
# 检查证书状态
sudo certbot certificates

# 手动续期
sudo certbot renew --dry-run
```

### 性能优化

#### 1. 数据库优化
```sql
-- 分析数据库性能
ANALYZE;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
```

#### 2. Nginx优化
```nginx
# 在nginx.conf中添加
worker_processes auto;
worker_connections 1024;

# 开启压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

## 📞 技术支持

### 联系方式
- 📧 Email: support@yourdomain.com
- 📚 文档: https://docs.yourdomain.com
- 🐛 Bug报告: https://github.com/your-repo/issues

### 日志收集
问题报告时请提供：
1. 系统版本信息
2. 错误日志
3. 复现步骤
4. 环境配置

```bash
# 收集系统信息
uname -a
cat /etc/os-release
sudo systemctl status userauth-api
sudo journalctl -u userauth-api --since "1 hour ago"
```

---

**注意**: 请在生产环境中：
1. 使用强密码
2. 定期更新系统
3. 监控服务状态
4. 定期备份数据
5. 及时应用安全更新
