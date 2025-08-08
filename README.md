# Prefect CI/CD 示例项目

这是一个基于 [Prefect](https://www.prefect.io/) 工作流编排平台的 CI/CD 示例项目，演示了如何使用 Prefect 进行自动化工作流部署和管理。

## 🚀 项目特性

- **自动化部署**: 通过 GitHub Actions 实现代码提交到自动部署的完整 CI/CD 流程
- **容器化**: 使用 Docker 确保环境一致性和可移植性，使用国内镜像源加速构建
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
cd <your-project-dir>
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并按需修改：

```bash
# Prefect 配置
PREFECT_API_URL=http://localhost:4200/api
WORK_POOL_NAME=my-docker-pool2

# Docker 镜像配置
IMAGE_REPO=ghcr.io/samples28/cicd-example
# IMAGE_TAG=v202501010000  # 可选

# 部署模式
DEPLOY_MODE=false
```

### 4. 配置 GitHub Secrets

在 GitHub 仓库设置中配置以下 secrets：

- `PREFECT_API_URL`: Prefect 服务器 API URL

说明：推送 GHCR 使用 `GITHUB_TOKEN`，默认已由 GitHub Actions 提供。

## 🚀 使用方法

### 本地运行

```bash
# 直接运行工作流
python flow.py

# 部署模式运行
DEPLOY_MODE=true python flow.py
```

### Docker 运行

项目提供两个Dockerfile选择（均使用国内镜像源加速）：
- `Dockerfile`: 简化版本，体积更小，推荐使用
- `Dockerfile.with-docker`: 包含Docker CLI，如果需要在容器内操作Docker时使用

**注意**: 如果在中国大陆地区构建遇到网络问题，请使用以下解决方案：

### 国内网络加速

已在镜像构建中使用清华镜像源（apt 与 pip），通常无需额外 hosts 配置。

```bash
# 构建镜像（简化版，推荐）
docker build -t cicd-example .

# 或构建包含Docker CLI的镜像（如果需要）
docker build -f Dockerfile.with-docker -t cicd-example:with-docker .

# 运行容器
docker run --rm \
  -e PREFECT_API_URL=http://172.31.0.55:4200/api \
  -e DEPLOY_MODE=true \
  cicd-example
```

### CI/CD 自动部署

项目配置了 GitHub Actions 工作流，当代码推送到 `main` 分支时会自动：

1. 构建 Docker 镜像
2. 推送到 GitHub Container Registry
3. 自动部署到 Prefect 服务器

## 📁 项目结构

```
.
├── .github/
│   └── workflows/
│       └── deploy-prefect-flow.yaml  # CI/CD 配置
├── flow.py                           # 入口：运行/部署
├── config.py                         # 配置管理
├── Dockerfile                        # 简化版镜像
├── Dockerfile.with-docker            # 包含 docker-cli 的镜像
├── pip.conf                          # pip 清华源配置
├── requirements.txt                  # Python 依赖
├── Makefile                          # 构建命令
├── README.md                         # 项目文档
├── .env.example                      # 环境变量示例
└── src/
    ├── flows.py                      # Prefect 流定义
    ├── deployment.py                 # 部署逻辑
    └── __init__.py
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
