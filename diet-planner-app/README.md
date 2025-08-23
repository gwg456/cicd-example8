# 减肥日程计划应用

一个集成了Microsoft Entra ID OIDC认证的现代化减肥管理应用，采用前后端分离架构。

## 功能特性

- 🔐 **Microsoft Entra ID OIDC 认证** - 安全的单点登录
- 📊 **数据可视化仪表板** - 直观的体重和营养摄入图表
- 🏃 **运动记录管理** - 记录和追踪运动数据
- 🍎 **饮食记录管理** - 详细的营养摄入记录
- ⚖️ **体重追踪** - 体重变化趋势分析
- 📋 **减肥计划制定** - 个性化的减肥目标设定
- 👤 **个人资料管理** - 完整的用户信息管理
- 📱 **响应式设计** - 支持桌面和移动设备

## 技术栈

### 后端
- **Flask** - Python Web框架
- **SQLAlchemy** - ORM数据库操作
- **Authlib** - OIDC认证库
- **Flask-CORS** - 跨域资源共享
- **PyJWT** - JWT令牌处理

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **Element Plus** - Vue 3组件库
- **Vue Router** - 路由管理
- **Pinia** - 状态管理
- **ECharts** - 数据可视化
- **Axios** - HTTP客户端
- **Vite** - 构建工具

### 数据库
- **SQLite** - 开发环境（可扩展到PostgreSQL/MySQL）

## 项目结构

```
diet-planner-app/
├── backend/                 # Flask后端
│   ├── routes/             # API路由
│   │   ├── auth_routes.py  # 认证相关路由
│   │   └── diet_routes.py  # 业务逻辑路由
│   ├── models.py           # 数据库模型
│   ├── auth.py             # 认证逻辑
│   ├── config.py           # 配置文件
│   ├── app.py              # Flask应用主文件
│   ├── init_db.py          # 数据库初始化脚本
│   ├── requirements.txt    # Python依赖
│   └── .env.example        # 环境变量模板
└── frontend/               # Vue3前端
    ├── src/
    │   ├── components/     # 共用组件
    │   ├── views/          # 页面组件
    │   ├── stores/         # Pinia状态管理
    │   ├── router/         # 路由配置
    │   └── main.js         # 应用入口
    ├── package.json        # 前端依赖
    ├── vite.config.js      # Vite配置
    └── index.html          # HTML入口
```

## 快速开始

### 前提条件

- Python 3.8+
- Node.js 16+
- Microsoft Azure账号（用于Entra ID配置）

### 1. 克隆项目

```bash
git clone <repository-url>
cd diet-planner-app
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\\Scripts\\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
cp .env.example .env
```

### 3. 配置Entra ID

1. 登录 [Azure Portal](https://portal.azure.com/)
2. 导航到 "Azure Active Directory" > "应用注册"
3. 点击 "新注册"
4. 填写应用信息：
   - 名称：Diet Planner App
   - 支持的账户类型：选择适合的选项
   - 重定向URI：`http://localhost:5000/auth/callback`
5. 记录以下信息：
   - 应用程序(客户端) ID
   - 目录(租户) ID
   - 客户端密钥（需要在"证书和密钥"中创建）

### 4. 配置环境变量

编辑 `backend/.env` 文件：

```env
# Flask配置
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///diet_planner.db

# Azure Entra ID配置
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_AUTHORITY=https://login.microsoftonline.com/your-tenant-id
AZURE_REDIRECT_URI=http://localhost:5000/auth/callback
AZURE_SCOPE=openid profile email

# 前端URL
FRONTEND_URL=http://localhost:3000

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
```

### 5. 初始化数据库

```bash
cd backend
python init_db.py
```

### 6. 启动后端服务

```bash
python app.py
```

后端服务将在 `http://localhost:5000` 启动

### 7. 前端设置

打开新的终端窗口：

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 `http://localhost:3000` 启动

## API文档

### 认证端点

- `GET /auth/login` - 启动OIDC登录流程
- `GET /auth/callback` - OIDC回调处理
- `GET /auth/user` - 获取当前用户信息
- `PUT /auth/user` - 更新用户信息
- `POST /auth/logout` - 用户登出
- `GET /auth/verify` - 验证JWT令牌

### 业务端点

- `GET /api/dashboard` - 获取仪表板数据
- `GET /api/diet-plans` - 获取减肥计划列表
- `POST /api/diet-plans` - 创建减肥计划
- `PUT /api/diet-plans/:id` - 更新减肥计划
- `GET /api/weight-records` - 获取体重记录
- `POST /api/weight-records` - 添加体重记录
- `GET /api/meal-records` - 获取饮食记录
- `POST /api/meal-records` - 添加饮食记录
- `GET /api/exercises` - 获取运动记录
- `POST /api/exercises` - 添加运动记录

## 部署

### 生产环境配置

1. **后端部署**：
   - 使用Gunicorn作为WSGI服务器
   - 配置Nginx作为反向代理
   - 使用PostgreSQL替代SQLite
   - 设置SSL证书

2. **前端部署**：
   - 构建生产版本：`npm run build`
   - 部署到CDN或静态文件服务器

### Docker部署（可选）

```dockerfile
# 后端Dockerfile示例
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
```

## 开发指南

### 代码规范

- 后端：遵循PEP 8 Python代码规范
- 前端：使用ESLint和Prettier进行代码格式化
- Git提交：使用约定式提交规范

### 测试

```bash
# 后端测试
cd backend
python -m pytest

# 前端测试
cd frontend
npm run test
```

## 贡献

1. Fork项目
2. 创建功能分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. 打开Pull Request

## 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情

## 支持

如果您遇到问题或有疑问，请：

1. 查看[文档](docs/)
2. 搜索[已有Issues](issues)
3. 创建新的[Issue](issues/new)

## 更新日志

查看[CHANGELOG.md](CHANGELOG.md)了解版本更新信息。