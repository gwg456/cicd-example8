# 生产环境部署指南

## 前端生产环境部署

### 方式一：传统部署（推荐）

#### 1. 构建生产版本

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build:prod
```

构建完成后，会在 `frontend/dist` 目录生成静态文件。

#### 2. 部署到Web服务器

**选项A：使用Nginx**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/diet-planner/dist;
    index index.html;

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API代理到后端
    location /api/ {
        proxy_pass http://your-backend-server:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 认证API代理
    location /auth/ {
        proxy_pass http://your-backend-server:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Vue Router历史模式支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

**选项B：使用Apache**

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /var/www/diet-planner/dist
    
    # 启用重写模块
    RewriteEngine On
    
    # Vue Router历史模式支持
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule . /index.html [L]
    
    # 静态资源缓存
    <LocationMatch "\.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$">
        ExpiresActive On
        ExpiresDefault "access plus 1 year"
    </LocationMatch>
    
    # API代理
    ProxyPass /api/ http://your-backend-server:5000/api/
    ProxyPassReverse /api/ http://your-backend-server:5000/api/
    
    ProxyPass /auth/ http://your-backend-server:5000/auth/
    ProxyPassReverse /auth/ http://your-backend-server:5000/auth/
</VirtualHost>
```

### 方式二：CDN部署

#### 部署到Vercel

```bash
# 安装Vercel CLI
npm i -g vercel

# 在frontend目录下
cd frontend
vercel

# 按提示配置项目
```

`vercel.json` 配置：

```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://your-backend-domain.com/api/$1"
    },
    {
      "src": "/auth/(.*)",
      "dest": "https://your-backend-domain.com/auth/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

#### 部署到Netlify

```bash
# 构建命令
npm run build:prod

# 发布目录
dist

# 重定向规则 (_redirects文件)
/api/*  https://your-backend-domain.com/api/:splat  200
/auth/* https://your-backend-domain.com/auth/:splat 200
/*      /index.html   200
```

### 方式三：Docker部署

#### 生产环境Dockerfile

```dockerfile
# 多阶段构建
FROM node:18-alpine as build-stage

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build:prod

# 生产阶段
FROM nginx:alpine as production-stage

# 复制构建文件
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.prod.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose生产配置

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    environment:
      - NODE_ENV=production
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/diet_planner
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: diet_planner
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

## 后端生产环境部署

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt gunicorn

# 设置生产环境变量
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@localhost:5432/diet_planner
```

### 2. 使用Gunicorn启动

```bash
# 基本启动
gunicorn --bind 0.0.0.0:5000 app:create_app()

# 生产配置
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --worker-class gevent \
         --worker-connections 1000 \
         --max-requests 1000 \
         --timeout 30 \
         --keep-alive 2 \
         --log-level info \
         --access-logfile - \
         --error-logfile - \
         app:create_app()
```

### 3. Systemd服务配置

创建 `/etc/systemd/system/diet-planner.service`：

```ini
[Unit]
Description=Diet Planner Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/diet-planner/backend
Environment=PATH=/var/www/diet-planner/backend/venv/bin
Environment=FLASK_ENV=production
ExecStart=/var/www/diet-planner/backend/venv/bin/gunicorn --bind unix:diet-planner.sock -m 007 app:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start diet-planner
sudo systemctl enable diet-planner
```

## 环境变量配置

### 生产环境 .env

```env
# Flask配置
FLASK_ENV=production
SECRET_KEY=your-super-secret-production-key
DATABASE_URL=postgresql://user:password@localhost:5432/diet_planner

# Azure Entra ID配置
AZURE_CLIENT_ID=your-production-client-id
AZURE_CLIENT_SECRET=your-production-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_AUTHORITY=https://login.microsoftonline.com/your-tenant-id
AZURE_REDIRECT_URI=https://your-domain.com/auth/callback
AZURE_SCOPE=openid profile email

# 前端URL
FRONTEND_URL=https://your-domain.com

# JWT配置
JWT_SECRET_KEY=your-jwt-production-secret-key

# 数据库配置
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

## 性能优化

### 前端优化

1. **代码分割**：已在vite.config.js中配置
2. **静态资源CDN**：将静态资源上传到CDN
3. **Gzip压缩**：Nginx配置中已启用
4. **缓存策略**：静态资源长期缓存

### 后端优化

1. **数据库连接池**
2. **Redis缓存**
3. **API响应缓存**
4. **数据库查询优化**

## 监控和日志

### 前端监控

```javascript
// 错误监控
window.addEventListener('error', (event) => {
  // 发送错误到监控服务
  console.error('Frontend Error:', event.error)
})

// 性能监控
window.addEventListener('load', () => {
  const perfData = performance.getEntriesByType('navigation')[0]
  console.log('Page Load Time:', perfData.loadEventEnd - perfData.fetchStart)
})
```

### 后端日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

if app.config['FLASK_ENV'] == 'production':
    file_handler = RotatingFileHandler('logs/diet-planner.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

## 安全配置

### HTTPS配置

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # 其他配置...
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 部署清单

### 部署前检查

- [ ] 更新生产环境配置
- [ ] 配置Entra ID生产应用
- [ ] 设置数据库
- [ ] 配置域名和SSL证书
- [ ] 测试所有API端点
- [ ] 验证认证流程

### 部署步骤

1. **前端部署**：
   ```bash
   npm run build:prod
   # 上传dist目录到服务器
   ```

2. **后端部署**：
   ```bash
   pip install -r requirements.txt
   python init_db.py
   gunicorn --bind 0.0.0.0:5000 app:create_app()
   ```

3. **配置反向代理**（Nginx/Apache）

4. **启动服务并测试**

这样就完成了完整的生产环境部署！