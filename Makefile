# Makefile for Prefect CI/CD Example Project

.PHONY: help install clean build run deploy

# 默认目标
help:
	@echo "可用的命令:"
	@echo "  install           - 安装项目依赖"
	@echo "  clean             - 清理临时文件"
	@echo "  build             - 构建 Docker 镜像（简化版）"
	@echo "  build-with-docker - 构建包含Docker CLI的镜像"
	@echo "  run               - 本地运行工作流"
	@echo "  deploy            - 部署工作流"

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
	python -c "from config import config; print('配置验证:', config.validate_config())"