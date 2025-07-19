# Prefect CI/CD 示例项目

这是一个基于 [Prefect](https://www.prefect.io/) 工作流编排平台的 CI/CD 示例项目，演示了如何使用 Prefect 进行自动化工作流部署和管理。

## 🚀 项目特性

- **自动化部署**: 通过 GitHub Actions 实现代码提交到自动部署的完整 CI/CD 流程
- **容器化**: 使用 Docker 确保环境一致性和可移植性
- **工作流编排**: 基于 Prefect 的强大工作流编排能力
- **定时调度**: 支持定时执行工作流任务
- **错误处理**: 完善的错误处理和超时机制
- **日志记录**: 详细的日志记录和监控

## 📋 系统要求

- Python 3.12+
- Docker
- Prefect 服务器或云服务
- GitHub 账户（用于 CI/CD）

## 🛠️ 安装和配置

### 1. 克隆项目

```bash
git clone <repository-url>
cd cicd-example
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件并配置以下环境变量：

```bash
# Prefect 配置
PREFECT_API_URL=http://your-prefect-server:4200/api
WORK_POOL_NAME=my-docker-pool2

# Docker 镜像配置
IMAGE_REPO=ghcr.io/your-username/cicd-example
IMAGE_TAG=v202501010000

# 部署模式
DEPLOY_MODE=false
```

### 4. 配置 GitHub Secrets

在 GitHub 仓库设置中配置以下 secrets：

- `PREFECT_API_URL`: Prefect 服务器 API URL
- `citoken`: GitHub Container Registry 访问令牌

## 🚀 使用方法

### 本地运行

```bash
# 直接运行工作流
python flow.py

# 部署模式运行
DEPLOY_MODE=true python flow.py
```

### Docker 运行

#### 标准构建
```bash
# 构建镜像
make build
# 或
docker build -t cicd-example .

# 运行容器
docker run --rm \
  -e PREFECT_API_URL=http://your-prefect-server:4200/api \
  -e DEPLOY_MODE=true \
  cicd-example
```

#### 多阶段构建（推荐）
```bash
# 构建优化镜像
make build-optimized
# 或
docker build -f Dockerfile.multi -t cicd-example:optimized .

# 运行优化容器
docker run --rm \
  -e PREFECT_API_URL=http://your-prefect-server:4200/api \
  -e DEPLOY_MODE=true \
  cicd-example:optimized
```

#### 生产环境构建
```bash
# 构建生产镜像
make build-prod
# 或
docker build -f Dockerfile.prod -t cicd-example:prod .

# 运行生产容器
docker run --rm \
  -e PREFECT_API_URL=http://your-prefect-server:4200/api \
  -e DEPLOY_MODE=true \
  cicd-example:prod
```

#### Docker Compose（推荐用于开发）
```bash
# 启动开发环境（包含 Prefect 服务器）
make compose-dev

# 启动生产环境
make compose-optimized

# 查看日志
make compose-logs

# 停止服务
make compose-down
```

### CI/CD 自动部署

项目配置了 GitHub Actions 工作流，当代码推送到 `main` 分支时会自动：

1. 构建 Docker 镜像
2. 推送到 GitHub Container Registry
3. 自动部署到 Prefect 服务器

## 📁 项目结构

```
cicd-example/
├── .github/
│   └── workflows/
│       └── deploy-prefect-flow.yaml  # CI/CD 配置
├── flow.py                           # 主要工作流代码
├── config.py                         # 配置文件
├── Dockerfile                        # 标准 Docker 镜像配置
├── Dockerfile.multi                  # 多阶段构建 Docker 镜像配置
├── Dockerfile.prod                   # 生产环境 Docker 镜像配置
├── docker-compose.yml                # Docker Compose 配置
├── .dockerignore                     # Docker 构建忽略文件
├── requirements.txt                  # Python 依赖
├── Makefile                          # 构建和部署命令
├── README.md                         # 项目文档
├── DOCKER_README.md                  # Docker 详细说明
└── .gitignore                        # Git 忽略文件
```

## 🔧 自定义配置

### 修改工作流

编辑 `flow.py` 中的 `hello()` 函数来自定义工作流逻辑：

```python
@flow(log_prints=True)
def hello():
    """自定义工作流逻辑"""
    print("你的自定义工作流")
    # 添加你的业务逻辑
```

### 修改调度配置

在部署函数中修改 `schedule` 参数：

```python
# 每小时执行
schedule={"interval": 3600}

# 每天执行
schedule={"interval": 86400}

# Cron 表达式
schedule={"cron": "0 9 * * *"}  # 每天上午9点
```

## 🐳 Docker 优化

本项目提供了多个优化版本的 Dockerfile：

### 版本对比

| 版本 | 用途 | 特点 | 推荐场景 |
|------|------|------|----------|
| `Dockerfile` | 标准版本 | 基础优化，易于理解 | 开发和测试 |
| `Dockerfile.multi` | 多阶段构建 | 镜像更小，构建更快 | CI/CD 和测试 |
| `Dockerfile.prod` | 生产版本 | 安全优化，权限控制 | 生产环境 |

### 主要优化点

1. **多阶段构建**: 分离构建和运行环境，减少镜像大小
2. **安全优化**: 使用非 root 用户，最小化依赖
3. **性能优化**: 合理使用缓存，优化环境变量
4. **健康检查**: 自动监控容器状态
5. **Docker Compose**: 简化开发和部署流程

详细说明请参考 [DOCKER_README.md](DOCKER_README.md)。

## 🐛 故障排除

### 常见问题

1. **Prefect API 连接失败**
   - 检查 `PREFECT_API_URL` 是否正确
   - 确认 Prefect 服务器正在运行
   - 检查网络连接

2. **Docker 构建失败**
   - 检查 Dockerfile 语法
   - 确认基础镜像可用
   - 检查网络连接

3. **部署超时**
   - 检查 Prefect 服务器响应时间
   - 增加超时配置
   - 检查网络延迟

### 日志查看

```bash
# 查看 Prefect 日志
prefect logs

# 查看容器日志
docker logs <container-id>
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如有问题或建议，请：

1. 查看 [Issues](../../issues) 页面
2. 创建新的 Issue
3. 联系项目维护者

---

**注意**: 这是一个示例项目，用于演示 Prefect CI/CD 的最佳实践。在生产环境中使用前，请根据实际需求进行适当的配置和测试。
