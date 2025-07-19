# Docker 优化说明

本项目提供了多个优化版本的 Dockerfile，以满足不同环境的需求。

## Dockerfile 版本说明

### 1. `Dockerfile` - 标准版本
- 基于官方 Python 3.12 slim 镜像
- 包含基本的安全优化
- 适合开发和测试环境

### 2. `Dockerfile.multi` - 多阶段构建版本
- 使用多阶段构建减少镜像大小
- 分离构建和运行环境
- 提高构建效率

### 3. `Dockerfile.prod` - 生产环境版本
- 包含额外的安全优化
- 更严格的权限控制
- 适合生产环境部署

## 构建命令

### 标准构建
```bash
# 使用标准 Dockerfile
make build

# 或直接使用 docker 命令
docker build -t cicd-example .
```

### 多阶段构建
```bash
# 使用多阶段构建
make build-optimized

# 或直接使用 docker 命令
docker build -f Dockerfile.multi -t cicd-example:optimized .
```

### 生产环境构建
```bash
# 构建生产环境镜像
make build-prod

# 或直接使用 docker 命令
docker build -f Dockerfile.prod -t cicd-example:prod .
```

## Docker Compose 使用

### 启动开发环境
```bash
# 启动包含 Prefect 服务器的完整开发环境
make compose-dev

# 或直接使用 docker-compose
docker-compose --profile dev up -d
```

### 启动生产环境
```bash
# 启动生产环境（使用多阶段构建）
make compose-optimized

# 或直接使用 docker-compose
docker-compose --profile optimized up -d
```

### 查看日志
```bash
make compose-logs
```

### 停止服务
```bash
make compose-down
```

## 环境变量配置

### 必需环境变量
- `PREFECT_API_URL`: Prefect API 服务器地址
- `IMAGE_REPO`: Docker 镜像仓库地址
- `WORK_POOL_NAME`: Prefect 工作池名称

### 可选环境变量
- `IMAGE_TAG`: Docker 镜像标签
- `DEPLOY_MODE`: 是否以部署模式运行
- `LOG_LEVEL`: 日志级别

## 镜像大小对比

| 版本 | 基础镜像 | 优化后大小 | 主要优化点 |
|------|----------|------------|------------|
| 原始版本 | python:3.12-slim | ~200MB | 基础优化 |
| 多阶段版本 | python:3.12-slim | ~150MB | 多阶段构建 |
| 生产版本 | python:3.12-slim | ~140MB | 安全优化 |

## 安全优化

### 1. 非 Root 用户
所有版本都使用非 root 用户运行应用，提高安全性。

### 2. 最小化依赖
只安装必要的系统依赖，减少攻击面。

### 3. 权限控制
严格控制文件权限，遵循最小权限原则。

### 4. 安全标签
生产版本包含安全相关的 Docker 标签。

## 性能优化

### 1. 多阶段构建
- 分离构建和运行环境
- 减少最终镜像大小
- 提高构建效率

### 2. 缓存优化
- 合理使用 Docker 层缓存
- 优化依赖安装顺序
- 使用 `.dockerignore` 减少构建上下文

### 3. 环境变量优化
- 设置 Python 相关环境变量
- 禁用不必要的功能
- 优化内存使用

## 健康检查

所有版本都包含健康检查配置：
- 检查间隔：30秒
- 超时时间：10秒
- 重试次数：3次
- 启动等待时间：5秒

## 故障排除

### 1. 构建失败
```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
make build
```

### 2. 运行失败
```bash
# 检查容器日志
docker logs <container_name>

# 检查健康状态
docker inspect <container_name> | grep Health
```

### 3. 权限问题
```bash
# 检查文件权限
docker exec <container_name> ls -la /app

# 重新设置权限
docker exec <container_name> chown -R appuser:appuser /app
```

## 最佳实践

1. **开发环境**：使用标准 Dockerfile 或 Docker Compose
2. **测试环境**：使用多阶段构建版本
3. **生产环境**：使用生产环境版本
4. **CI/CD**：使用多阶段构建提高构建效率
5. **安全扫描**：定期对镜像进行安全扫描

## 更新日志

- **v1.0**: 初始版本，包含基本优化
- **v1.1**: 添加多阶段构建
- **v1.2**: 添加生产环境版本
- **v1.3**: 添加 Docker Compose 支持