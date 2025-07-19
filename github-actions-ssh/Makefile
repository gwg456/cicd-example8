# GitHub Actions SSH 使用指南 - Makefile

.PHONY: help install install-deps pdf pdf-single pdf-batch clean test setup verify all

# 默认目标
help:
	@echo "📚 GitHub Actions SSH 使用指南 - 可用命令"
	@echo ""
	@echo "🔧 安装和设置:"
	@echo "  make install       - 完整安装（依赖 + SSH 设置）"
	@echo "  make install-deps  - 仅安装依赖"
	@echo "  make setup         - SSH 密钥设置"
	@echo "  make verify        - 验证安装"
	@echo "  make test          - 运行测试"
	@echo ""
	@echo "📄 PDF 生成:"
	@echo "  make pdf           - 生成主要 PDF 文档"
	@echo "  make pdf-single    - 生成单个文件 PDF（FILE=文件名）"
	@echo "  make pdf-batch     - 批量生成所有 PDF"
	@echo "  make pdf-compress  - 批量生成并压缩 PDF"
	@echo ""
	@echo "🧹 清理:"
	@echo "  make clean         - 清理生成的文件"
	@echo "  make clean-all     - 清理所有临时文件"
	@echo ""
	@echo "📦 发布:"
	@echo "  make package       - 打包所有文档"
	@echo "  make release       - 创建发布版本"
	@echo ""
	@echo "示例:"
	@echo "  make pdf-single FILE=README.md"
	@echo "  make pdf-batch"

# 变量定义
SCRIPTS_DIR = scripts
OUTPUT_DIR = output
DOCS_DIR = docs
PDF_GENERATOR = $(SCRIPTS_DIR)/generate-pdf.py
BATCH_GENERATOR = $(SCRIPTS_DIR)/batch-generate-pdf.sh
INSTALL_SCRIPT = $(SCRIPTS_DIR)/install-dependencies.sh
SSH_SETUP_SCRIPT = $(SCRIPTS_DIR)/setup-ssh-keys.sh

# 检查 Python 环境
check-python:
	@echo "🐍 检查 Python 环境..."
	@python3 --version || (echo "❌ Python 3 未安装" && exit 1)
	@pip3 --version || (echo "❌ pip3 未安装" && exit 1)

# 安装依赖
install-deps:
	@echo "📦 安装依赖包..."
	@chmod +x $(INSTALL_SCRIPT)
	@$(INSTALL_SCRIPT)

# SSH 密钥设置
setup:
	@echo "🔐 SSH 密钥设置..."
	@chmod +x $(SSH_SETUP_SCRIPT)
	@$(SSH_SETUP_SCRIPT)

# 完整安装
install: install-deps
	@echo "✅ 安装完成！"

# 验证安装
verify:
	@echo "🔍 验证安装..."
	@chmod +x $(INSTALL_SCRIPT)
	@$(INSTALL_SCRIPT) --verify

# 运行测试
test: verify
	@echo "🧪 运行测试..."
	@chmod +x $(INSTALL_SCRIPT)
	@$(INSTALL_SCRIPT) --test

# 生成主要 PDF 文档
pdf: check-python
	@echo "📄 生成主要 PDF 文档..."
	@mkdir -p $(OUTPUT_DIR)
	@python3 $(PDF_GENERATOR) README.md -o $(OUTPUT_DIR)/GitHub-Actions-SSH-指南.pdf
	@echo "✅ PDF 生成完成: $(OUTPUT_DIR)/GitHub-Actions-SSH-指南.pdf"

# 生成单个文件 PDF
pdf-single: check-python
ifndef FILE
	@echo "❌ 请指定文件名: make pdf-single FILE=文件名.md"
	@exit 1
endif
	@echo "📄 生成 PDF: $(FILE)"
	@mkdir -p $(OUTPUT_DIR)
	@python3 $(PDF_GENERATOR) $(FILE) -o $(OUTPUT_DIR)/$(basename $(FILE)).pdf
	@echo "✅ PDF 生成完成: $(OUTPUT_DIR)/$(basename $(FILE)).pdf"

# 批量生成 PDF
pdf-batch: check-python
	@echo "📚 批量生成 PDF..."
	@chmod +x $(BATCH_GENERATOR)
	@$(BATCH_GENERATOR) . $(OUTPUT_DIR)

# 批量生成并压缩 PDF
pdf-compress: check-python
	@echo "📚 批量生成并压缩 PDF..."
	@chmod +x $(BATCH_GENERATOR)
	@$(BATCH_GENERATOR) -c -i . $(OUTPUT_DIR)

# 创建文档目录结构
docs-structure:
	@echo "📁 创建文档目录结构..."
	@mkdir -p $(DOCS_DIR)/images
	@mkdir -p $(DOCS_DIR)/examples
	@mkdir -p $(DOCS_DIR)/templates
	@mkdir -p $(OUTPUT_DIR)/pdf
	@mkdir -p $(OUTPUT_DIR)/html

# 生成 HTML 文档
html: check-python docs-structure
	@echo "🌐 生成 HTML 文档..."
	@python3 -c "
import markdown
import os

# 读取 README
with open('README.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 转换为 HTML
md = markdown.Markdown(extensions=['codehilite', 'fenced_code', 'tables', 'toc'])
html_content = md.convert(content)

# 生成完整 HTML
full_html = f'''<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>GitHub Actions SSH 使用指南</title>
    <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css\">
    <style>
        .markdown-body {{ box-sizing: border-box; min-width: 200px; max-width: 980px; margin: 0 auto; padding: 45px; }}
    </style>
</head>
<body>
    <article class=\"markdown-body\">
        {html_content}
    </article>
</body>
</html>'''

# 保存 HTML
with open('$(OUTPUT_DIR)/GitHub-Actions-SSH-指南.html', 'w', encoding='utf-8') as f:
    f.write(full_html)
"
	@echo "✅ HTML 生成完成: $(OUTPUT_DIR)/GitHub-Actions-SSH-指南.html"

# 清理生成的文件
clean:
	@echo "🧹 清理生成的文件..."
	@rm -f *.pdf
	@rm -f test-document.*
	@rm -rf $(OUTPUT_DIR)
	@echo "✅ 清理完成"

# 清理所有临时文件
clean-all: clean
	@echo "🧹 清理所有临时文件..."
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@rm -f *.pyc
	@find . -name "*.tmp" -delete
	@find . -name ".DS_Store" -delete
	@echo "✅ 全部清理完成"

# 打包文档
package: pdf-compress html
	@echo "📦 打包文档..."
	@mkdir -p releases
	@tar -czf releases/github-actions-ssh-guide-$(shell date +%Y%m%d).tar.gz \
		README.md \
		$(OUTPUT_DIR) \
		.github/workflows \
		scripts \
		requirements.txt \
		Makefile
	@echo "✅ 打包完成: releases/github-actions-ssh-guide-$(shell date +%Y%m%d).tar.gz"

# 创建发布版本
release: package
	@echo "🚀 创建发布版本..."
	@echo "版本信息:" > RELEASE_NOTES.md
	@echo "- 生成时间: $(shell date)" >> RELEASE_NOTES.md
	@echo "- Git 提交: $(shell git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" >> RELEASE_NOTES.md
	@echo "- 包含文档: GitHub Actions SSH 使用指南" >> RELEASE_NOTES.md
	@echo "- 格式: PDF, HTML" >> RELEASE_NOTES.md
	@echo "✅ 发布版本创建完成"

# 开发环境设置
dev-setup: install-deps
	@echo "🛠️ 设置开发环境..."
	@pip3 install pre-commit black flake8 pytest
	@echo "✅ 开发环境设置完成"

# 代码格式化
format:
	@echo "🎨 格式化代码..."
	@black $(SCRIPTS_DIR)/*.py
	@echo "✅ 代码格式化完成"

# 代码检查
lint:
	@echo "🔍 代码检查..."
	@flake8 $(SCRIPTS_DIR)/*.py --max-line-length=88
	@echo "✅ 代码检查完成"

# 运行所有检查
check: lint test
	@echo "✅ 所有检查通过"

# 显示项目信息
info:
	@echo "📊 项目信息"
	@echo "============="
	@echo "项目名称: GitHub Actions SSH 使用指南"
	@echo "描述: 完整的 SSH 密钥配置与自动化部署指南"
	@echo ""
	@echo "📁 目录结构:"
	@find . -type f -name "*.md" -o -name "*.py" -o -name "*.sh" -o -name "*.yml" | head -20
	@echo ""
	@echo "📄 文档统计:"
	@echo "Markdown 文件: $(shell find . -name "*.md" | wc -l)"
	@echo "Python 脚本: $(shell find . -name "*.py" | wc -l)"
	@echo "Shell 脚本: $(shell find . -name "*.sh" | wc -l)"
	@echo "GitHub Actions: $(shell find .github/workflows -name "*.yml" 2>/dev/null | wc -l)"

# 显示状态
status:
	@echo "🔍 项目状态"
	@echo "============"
	@echo "Python 环境:"
	@python3 --version 2>/dev/null || echo "  ❌ Python 3 未安装"
	@pip3 --version 2>/dev/null || echo "  ❌ pip3 未安装"
	@echo ""
	@echo "依赖检查:"
	@python3 -c "import markdown; print('  ✅ markdown:', markdown.__version__)" 2>/dev/null || echo "  ❌ markdown 未安装"
	@python3 -c "import weasyprint; print('  ✅ weasyprint:', weasyprint.__version__)" 2>/dev/null || echo "  ❌ weasyprint 未安装"
	@echo ""
	@echo "输出目录:"
	@if [ -d "$(OUTPUT_DIR)" ]; then echo "  ✅ $(OUTPUT_DIR) 存在"; else echo "  ❌ $(OUTPUT_DIR) 不存在"; fi
	@echo ""
	@echo "生成的文件:"
	@find $(OUTPUT_DIR) -name "*.pdf" 2>/dev/null | wc -l | xargs echo "  PDF 文件:"
	@find $(OUTPUT_DIR) -name "*.html" 2>/dev/null | wc -l | xargs echo "  HTML 文件:"

# 快速开始
quickstart:
	@echo "🚀 快速开始指南"
	@echo "================"
	@echo ""
	@echo "1️⃣ 安装依赖:"
	@echo "   make install-deps"
	@echo ""
	@echo "2️⃣ 生成 PDF:"
	@echo "   make pdf"
	@echo ""
	@echo "3️⃣ 设置 SSH 密钥:"
	@echo "   make setup"
	@echo ""
	@echo "4️⃣ 查看所有命令:"
	@echo "   make help"

# 一键部署
all: install pdf-compress
	@echo "🎉 一键部署完成！"
	@echo ""
	@echo "生成的文件:"
	@ls -la $(OUTPUT_DIR)/*.pdf 2>/dev/null || echo "  没有 PDF 文件"
	@echo ""
	@echo "下一步："
	@echo "  1. 查看生成的 PDF: $(OUTPUT_DIR)/"
	@echo "  2. 设置 SSH 密钥: make setup"
	@echo "  3. 查看完整指南: make help"