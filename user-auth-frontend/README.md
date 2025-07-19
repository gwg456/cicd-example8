# 用户认证系统 - 前端

基于 Vue 3 + Element Plus 的现代化用户认证管理系统前端应用。

## 🚀 功能特性

- ✅ **用户认证**: 注册、登录、退出
- ✅ **个人资料管理**: 查看和编辑个人信息
- ✅ **角色权限控制**: 基于角色的访问控制 (RBAC)
- ✅ **用户管理**: 管理员可以管理所有用户
- ✅ **角色管理**: 超级管理员可以管理角色
- ✅ **响应式设计**: 支持桌面端和移动端
- ✅ **现代化UI**: 基于 Element Plus 的美观界面

## 🛠️ 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **UI库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **CSS预处理器**: 原生CSS + CSS变量

## 📋 系统要求

- Node.js 16+ 
- npm 7+ 或 yarn 1.22+

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
# 或
yarn install
```

### 2. 环境配置

复制环境变量文件并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# API Base URL
VITE_API_BASE_URL=http://localhost:8000

# App Title
VITE_APP_TITLE=用户认证系统

# App Version
VITE_APP_VERSION=1.0.0
```

### 3. 启动开发服务器

```bash
npm run dev
# 或
yarn dev
```

应用将在 http://localhost:3000 启动

### 4. 构建生产版本

```bash
npm run build
# 或
yarn build
```

## 📁 项目结构

```
src/
├── api/               # API 接口封装
│   ├── http.js       # HTTP 客户端配置
│   ├── auth.js       # 认证相关接口
│   ├── users.js      # 用户管理接口
│   └── roles.js      # 角色管理接口
├── components/       # 公共组件
│   └── Layout.vue    # 主布局组件
├── router/           # 路由配置
│   └── index.js      # 路由定义
├── stores/           # 状态管理
│   └── auth.js       # 认证状态
├── views/            # 页面组件
│   ├── Login.vue     # 登录页
│   ├── Register.vue  # 注册页
│   ├── Dashboard.vue # 仪表板
│   ├── Profile.vue   # 个人资料
│   └── admin/        # 管理员页面
│       ├── Users.vue # 用户管理
│       └── Roles.vue # 角色管理
├── App.vue           # 根组件
└── main.js           # 应用入口
```

## 🔐 权限系统

### 角色类型

- **superuser**: 超级管理员，拥有所有权限
- **admin**: 管理员，可以管理用户和角色
- **manager**: 经理，可以查看用户列表
- **user**: 普通用户，只能管理自己的资料

### 路由守卫

- **requiresAuth**: 需要登录才能访问
- **requiresAdmin**: 需要管理员权限
- **hideForAuth**: 已登录用户隐藏（如登录、注册页）

## 🎨 主题和样式

项目使用 Element Plus 默认主题，支持：

- 响应式布局
- 深色模式（可扩展）
- 自定义主色调
- 移动端适配

## 📱 移动端支持

- 响应式设计，支持各种屏幕尺寸
- 触摸友好的交互
- 移动端优化的表格和表单

## 🔧 开发工具

### 推荐的 VSCode 扩展

- Vetur 或 Volar (Vue 3 支持)
- ESLint
- Prettier
- Auto Rename Tag

### 代码规范

项目使用 ESLint + Prettier 进行代码规范化：

```bash
# 检查代码规范
npm run lint

# 格式化代码
npm run format
```

## 🚀 部署

### 构建

```bash
npm run build
```

### 部署到 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔗 相关链接

- [Vue 3 文档](https://v3.vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Vite 文档](https://vitejs.dev/)
- [Pinia 文档](https://pinia.vuejs.org/)

## 📝 更新日志

### v1.0.0 (2024-01-01)

- ✨ 初始版本发布
- ✨ 完整的用户认证功能
- ✨ 角色权限管理
- ✨ 响应式设计
- ✨ 现代化UI界面

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE)