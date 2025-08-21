# Makefile for Prefect CI/CD Example Project

.PHONY: help install clean build run deploy test

# 默认目标
help:
	@echo "📋 Prefect CI/CD 项目 - 可用命令:"
	@echo ""
	@echo "🔧 开发命令:"
	@echo "  install           - 安装项目依赖"
	@echo "  install-dev       - 安装开发依赖"
	@echo "  dev-setup         - 开发环境设置"
	@echo "  clean             - 清理临时文件"
	@echo "  deps-update       - 更新依赖锁定文件"
	@echo ""
	@echo "🧪 测试命令:"
	@echo "  test              - 运行所有测试"
	@echo "  test-unit         - 运行单元测试"
	@echo "  test-integration  - 运行集成测试"
	@echo "  test-e2e          - 运行端到端测试"
	@echo "  test-cov          - 运行测试并生成覆盖率报告"
	@echo ""
	@echo "🔍 代码质量命令:"
	@echo "  lint              - 检查代码风格"
	@echo "  format            - 自动格式化代码"
	@echo "  type-check        - 类型检查"
	@echo "  security-check    - 安全检查"
	@echo "  pre-commit        - 运行pre-commit检查"
	@echo ""
	@echo "🐳 Docker 命令:"
	@echo "  build             - 构建 Docker 镜像"
	@echo "  build-dev         - 构建开发版Docker镜像"
	@echo "  docker-run        - 运行 Docker 容器"
	@echo "  docker-deploy     - 部署 Docker 容器"
	@echo ""
	@echo "🚀 运行命令:"
	@echo "  run               - 本地运行工作流"
	@echo "  deploy            - 部署工作流"
	@echo "  cli               - 显示CLI帮助"
	@echo ""
	@echo "🔍 检查命令:"
	@echo "  health            - 健康检查"
	@echo "  validate          - 验证配置"
	@echo "  config-summary    - 显示配置摘要"
	@echo "  test-connection   - 测试 Prefect 连接"
	@echo "  status            - 检查项目状态"
	@echo "  check             - 完整的项目检查"
	@echo "  metrics           - 显示应用指标"

# 安装依赖
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

deps-update:
	python scripts/manage_deps.py update-lock

# 测试命令
test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# 代码质量
lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy src/ --ignore-missing-imports

security-check:
	python scripts/manage_deps.py check-security

pre-commit:
	pre-commit run --all-files

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# 构建 Docker 镜像
build:
	docker build -t cicd-example .

build-dev:
	docker build -t cicd-example:dev --target builder .

# 本地运行工作流
run:
	python flow.py

# 使用CLI运行
cli:
	python -m src.cli --help

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
dev-setup: install-dev
	pre-commit install

# 健康检查
health:
	python -m src.cli health

# 检查项目状态
status:
	@echo "📊 项目状态检查:"
	@echo "Python 版本: $(shell python --version)"
	@echo "Docker 版本: $(shell docker --version 2>/dev/null || echo 'Docker 未安装')"
	@echo "Git 版本: $(shell git --version 2>/dev/null || echo 'Git 未安装')"
	@echo ""
	@echo "📦 Python 包信息:"
	@pip list | grep -E "(prefect|ruff|pytest)" || echo "相关包未安装"
	@echo ""
	@echo "🔧 开发工具状态:"
	@which pre-commit >/dev/null 2>&1 && echo "✅ pre-commit 已安装" || echo "❌ pre-commit 未安装"
	@which mypy >/dev/null 2>&1 && echo "✅ mypy 已安装" || echo "❌ mypy 未安装"

# 验证配置
validate:
	@echo "🔍 验证配置..."
	@python -m src.cli config-info

# 显示配置摘要
config-summary:
	@python -m src.cli config-info

# 显示指标
metrics:
	@python -m src.cli metrics

# 测试 Prefect 连接
test-connection:
	@echo "🔗 测试 Prefect 连接..."
	@python -c "import asyncio; from src.deployment import DeploymentManager; result = asyncio.run(DeploymentManager().check_prefect_connection()); print('✅ 连接成功' if result else '❌ 连接失败')"

# 完整的项目检查
check: validate status health
	@echo ""
	@echo "✅ 项目检查完成"

# 质量检查（用于CI）
quality-check: lint type-check security-check test-unit
	@echo "✅ 代码质量检查完成"

# 发布前检查
pre-release: clean quality-check test build
	@echo "✅ 发布前检查完成"
