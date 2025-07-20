# 🚀 FastAPI用户服务 - JWT认证系统

## 📋 项目概述

基于FastAPI构建的现代化用户管理服务，提供用户注册、登录、JWT认证等完整功能。

## 🎯 核心功能

### ✨ 主要特性
- **用户注册**: 安全的用户注册接口
- **用户登录**: JWT Token认证登录
- **密码加密**: bcrypt安全密码哈希
- **JWT认证**: 完整的Token认证体系
- **数据验证**: Pydantic模型验证
- **API文档**: 自动生成OpenAPI文档
- **单元测试**: 完整的测试覆盖
- **数据库**: SQLAlchemy ORM + SQLite

### 📊 接口列表
```
POST   /user/register    # 用户注册
POST   /user/login       # 用户登录
GET    /user/profile     # 获取用户信息 (需要认证)
PUT    /user/profile     # 更新用户信息 (需要认证)
POST   /auth/refresh     # 刷新JWT Token
GET    /health           # 健康检查
```

## 🛠️ 技术栈

### 🔧 后端框架
- **FastAPI**: 现代化Python Web框架
- **SQLAlchemy**: ORM数据库工具
- **Pydantic**: 数据验证和序列化
- **PyJWT**: JWT Token处理
- **bcrypt**: 密码加密
- **python-multipart**: 文件上传支持

### 🗄️ 数据库
- **SQLite**: 轻量级数据库（开发环境）
- **PostgreSQL**: 生产环境推荐
- **MySQL**: 可选数据库

### 🧪 测试工具
- **pytest**: 单元测试框架
- **httpx**: 异步HTTP客户端
- **pytest-asyncio**: 异步测试支持

## 📦 项目结构

```
fastapi-user-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py              # 配置管理
│   ├── database.py            # 数据库连接
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py            # 用户数据模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py            # 用户Pydantic模型
│   │   └── auth.py            # 认证相关模型
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── user.py            # 用户路由
│   │   └── auth.py            # 认证路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py    # 用户业务逻辑
│   │   └── auth_service.py    # 认证业务逻辑
│   └── utils/
│       ├── __init__.py
│       ├── security.py        # 安全工具
│       └── dependencies.py    # 依赖注入
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # 测试配置
│   ├── test_user.py           # 用户接口测试
│   └── test_auth.py           # 认证接口测试
├── docs/
│   ├── api_spec.yaml          # OpenAPI规范
│   └── database_schema.sql    # 数据库Schema
├── requirements.txt           # Python依赖
├── docker-compose.yml         # Docker配置
├── Dockerfile                 # Docker镜像
└── README.md                  # 项目说明
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化
```bash
# 创建数据库表
python -c "from app.database import create_tables; create_tables()"
```

### 3. 启动服务
```bash
# 开发模式启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式启动
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 4. 访问API文档
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI规范**: http://localhost:8000/openapi.json

## 📖 API使用示例

### 用户注册
```bash
curl -X POST "http://localhost:8000/user/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123",
    "full_name": "Test User"
  }'
```

### 用户登录
```bash
curl -X POST "http://localhost:8000/user/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=securepassword123"
```

### 获取用户信息
```bash
curl -X GET "http://localhost:8000/user/profile" \
  -H "Authorization: Bearer your-jwt-token"
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_user.py

# 生成测试覆盖率报告
pytest --cov=app --cov-report=html
```

## 🐳 Docker部署

```bash
# 构建镜像
docker build -t fastapi-user-service .

# 运行容器
docker run -p 8000:8000 fastapi-user-service

# 使用docker-compose
docker-compose up -d
```

## 🔧 配置说明

### 环境变量
```bash
# 数据库配置
DATABASE_URL=sqlite:///./users.db

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
DEBUG=True
APP_NAME=FastAPI User Service
VERSION=1.0.0
```

## 🔐 安全特性

### 密码安全
- bcrypt哈希加密
- 盐值自动生成
- 密码强度验证

### JWT安全
- 安全的密钥管理
- Token过期时间控制
- 自动Token刷新

### API安全
- 输入数据验证
- SQL注入防护
- CORS配置

## 📊 监控与日志

### 日志配置
- 结构化日志输出
- 不同级别日志分离
- 敏感信息脱敏

### 健康检查
- 数据库连接检查
- 服务状态监控
- 性能指标收集

## 🔄 扩展功能

### 可扩展特性
- 邮箱验证
- 手机号验证
- 第三方登录
- 角色权限管理
- 密码重置
- 用户头像上传

## 📞 技术支持

如有问题，请参考：
- FastAPI官方文档
- SQLAlchemy文档
- JWT最佳实践
- Python安全指南