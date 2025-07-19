# Makefile for Prefect CI/CD Example Project

.PHONY: help install test lint format clean build run deploy

# 默认目标
help:
	@echo "可用的命令:"
	@echo "  install    - 安装项目依赖"
	@echo "  test       - 运行测试"
	@echo "  lint       - 代码检查"
	@echo "  format     - 代码格式化"
	@echo "  clean      - 清理临时文件"
	@echo "  build      - 构建 Docker 镜像"
	@echo "  run        - 本地运行工作流"
	@echo "  deploy     - 部署工作流"

# 安装依赖
install:
	pip install -r requirements.txt

# 运行测试
test:
	pytest tests/ -v --cov=flow --cov=config --cov-report=html

# 代码检查
lint:
	flake8 flow.py config.py tests/
	mypy flow.py config.py

# 代码格式化
format:
	black flow.py config.py tests/
	isort flow.py config.py tests/

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# 构建 Docker 镜像
build:
	docker build -t cicd-example .

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
	pre-commit install

# 检查项目状态
status:
	@echo "项目状态检查:"
	@echo "Python 版本: $(shell python --version)"
	@echo "Docker 版本: $(shell docker --version)"
	@echo "Prefect 版本: $(shell prefect version)"
	@echo "已安装的包:"
	@pip list | grep -E "(prefect|pytest|black|flake8)"

# 验证配置
validate:
	python -c "from config import config; print('配置验证:', config.validate_config())"