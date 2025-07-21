# Makefile for Prefect CI/CD Example Project

.PHONY: help install clean build run deploy

# 默认目标
help:
	@echo "📋 Prefect CI/CD 项目 - 可用命令:"
	@echo ""
	@echo "🔧 开发命令:"
	@echo "  install           - 安装项目依赖"
	@echo "  dev-setup         - 开发环境设置"
	@echo "  clean             - 清理临时文件"
	@echo ""
	@echo "🐳 Docker 命令:"
	@echo "  build             - 构建 Docker 镜像（简化版）"
	@echo "  build-with-docker - 构建包含Docker CLI的镜像"
	@echo "  docker-run        - 运行 Docker 容器"
	@echo "  docker-deploy     - 部署 Docker 容器"
	@echo ""
	@echo "🚀 运行命令:"
	@echo "  run               - 本地运行工作流"
	@echo "  deploy            - 部署工作流"
	@echo ""
	@echo "🔍 检查命令:"
	@echo "  validate          - 验证配置"
	@echo "  config-summary    - 显示配置摘要"
	@echo "  test-connection   - 测试 Prefect 连接"
	@echo "  status            - 检查项目状态"
	@echo "  check             - 完整的项目检查"

# 安装依赖
install:
	pip install -r requirements.txt

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# 构建 Docker 镜像
build:
	docker build -t cicd-example .

# 构建包含Docker CLI的镜像
build-with-docker:
	docker build -f Dockerfile.with-docker -t cicd-example:with-docker .

# 本地运行工作流
run:
	python flow.py

# 部署工作流
deploy:
	DEPLOY_MODE=true python flow.py

# 运行 Docker 容器
docker-run:
	docker run --rm \
		-e PREFECT_API_URL=http://localhost:4200/api \
		-e DEPLOY_MODE=false \
		cicd-example

# 部署 Docker 容器
docker-deploy:
	docker run --rm \
		-e PREFECT_API_URL=http://localhost:4200/api \
		-e DEPLOY_MODE=true \
		-v /var/run/docker.sock:/var/run/docker.sock \
		cicd-example

# 开发环境设置
dev-setup: install

# 检查项目状态
status:
	@echo "项目状态检查:"
	@echo "Python 版本: $(shell python --version)"
	@echo "Docker 版本: $(shell docker --version)"
	@echo "Prefect 版本: $(shell prefect version)"
	@echo "已安装的包:"
	@pip list | grep prefect

# 验证配置
validate:
	python -c "from config import config; missing = config.validate_required_settings(); print('配置验证:', '✅ 通过' if not missing else f'❌ 缺少: {missing}')"

# 显示配置摘要
config-summary:
	python -c "from config import config; import json; print('配置摘要:'); print(json.dumps(config.get_config_summary(), indent=2, ensure_ascii=False))"

# 测试 Prefect 连接
test-connection:
	python -c "import asyncio; from src.deployment import DeploymentManager; asyncio.run(DeploymentManager().check_prefect_connection())"

# 完整的项目检查
check: validate config-summary status
	@echo "✅ 项目检查完成"