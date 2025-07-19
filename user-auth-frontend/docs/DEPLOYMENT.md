# 前端部署配置说明

## 🌍 环境变量配置

### 开发环境 (.env)
```bash
# API Base URL (开发环境通过代理访问)
VITE_API_BASE_URL=http://localhost:8000

# App Title
VITE_APP_TITLE=用户认证系统 [开发环境]

# App Version
VITE_APP_VERSION=1.0.0-dev

# Debug Mode
VITE_DEBUG=true
```

### 生产环境 (.env.production.local)
```bash
# API Base URL (留空使用当前域名)
VITE_API_BASE_URL=

# 或者指定具体的API服务器地址
# VITE_API_BASE_URL=https://api.yourdomain.com

# App Title
VITE_APP_TITLE=用户认证系统

# App Version
VITE_APP_VERSION=1.0.0

# Debug Mode
VITE_DEBUG=false
```

## 📡 API地址配置策略

### 1. 同域名部署 (推荐)
前端和后端部署在同一域名下，通过Nginx反向代理：

```
https://yourdomain.com/          -> 前端静态文件
https://yourdomain.com/api/      -> 后端API
```

配置：
```bash
VITE_API_BASE_URL=
```

### 2. 不同域名部署
前端和后端分别部署在不同域名：

```
https://app.yourdomain.com/      -> 前端
https://api.yourdomain.com/      -> 后端API
```

配置：
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
```

### 3. 本地开发
开发环境使用Vite代理：

```
http://localhost:3000/           -> 前端开发服务器
http://localhost:3000/api/       -> 代理到后端 (localhost:8000)
```

配置：
```bash
VITE_API_BASE_URL=http://localhost:8000
```

## 🔧 构建和部署

### 开发环境启动
```bash
npm install
npm run dev
```

### 生产环境构建
```bash
# 设置环境变量
cp .env.production.example .env.production.local
# 编辑 .env.production.local 设置正确的API地址

# 构建
npm run build

# 预览构建结果
npm run preview
```

### 部署到服务器
```bash
# 1. 上传dist目录到服务器
scp -r dist/* user@server:/var/www/userauth/

# 2. 或使用rsync
rsync -av --delete dist/ user@server:/var/www/userauth/
```

## 🌐 Nginx配置示例

### 同域名部署
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    root /var/www/userauth;
    index index.html;
    
    # 静态文件
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 跨域配置 (不同域名)
如果前后端不在同一域名，需要配置CORS：

后端配置 (app/main.py):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.yourdomain.com"],  # 前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔍 调试和故障排除

### 1. API连接问题
检查浏览器开发者工具的Network标签：
- 检查API请求的URL是否正确
- 查看是否有CORS错误
- 检查响应状态码

### 2. 环境变量不生效
确保环境变量以`VITE_`开头：
```bash
# ✅ 正确
VITE_API_BASE_URL=https://api.example.com

# ❌ 错误
API_BASE_URL=https://api.example.com
```

### 3. 代理不工作
检查vite.config.js中的代理配置：
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

### 4. 生产环境API 404
确保Nginx正确配置了API代理：
```nginx
location /api/ {
    proxy_pass http://localhost:8000;
    # 注意：proxy_pass末尾不要加/
}
```

## 📊 环境检查命令

### 检查当前配置
在浏览器控制台运行：
```javascript
console.log('API Base URL:', window.location.origin + '/api/v1')
console.log('Environment:', import.meta.env.MODE)
console.log('Debug Mode:', import.meta.env.VITE_DEBUG)
```

### 测试API连接
```javascript
fetch('/api/v1/health')
  .then(response => response.json())
  .then(data => console.log('API Health:', data))
  .catch(error => console.error('API Error:', error))
```

## 🚀 自动化部署

### 使用GitHub Actions
创建 `.github/workflows/deploy.yml`:
```yaml
name: Deploy Frontend

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: npm install
      
    - name: Build
      run: |
        echo "VITE_API_BASE_URL=" > .env.production.local
        echo "VITE_APP_TITLE=用户认证系统" >> .env.production.local
        echo "VITE_APP_VERSION=${GITHUB_SHA:0:7}" >> .env.production.local
        npm run build
        
    - name: Deploy to server
      run: |
        # 部署到服务器的脚本
        rsync -av --delete dist/ user@server:/var/www/userauth/
```

## 📝 配置检查清单

部署前请检查：

- [ ] 环境变量文件已正确配置
- [ ] API Base URL指向正确的后端服务
- [ ] CORS配置已设置（如果跨域）
- [ ] Nginx配置已更新
- [ ] SSL证书已配置
- [ ] 静态文件权限正确
- [ ] API健康检查正常

## 🔗 相关链接

- [Vite环境变量文档](https://vitejs.dev/guide/env-and-mode.html)
- [Vue3生产部署指南](https://v3.vuejs.org/guide/installation.html#production-deployment)
- [Nginx反向代理配置](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)