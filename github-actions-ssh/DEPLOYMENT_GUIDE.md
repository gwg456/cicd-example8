# 🚀 GitLab 部署指南

## 📋 概述

本指南详细说明如何将 GitHub Actions SSH 使用指南项目部署到 GitLab，并自动生成 PDF 文档。

## 🔧 准备工作

### 1. GitLab 访问令牌

首先需要创建 GitLab 个人访问令牌：

1. 访问 GitLab: https://gitlab.com
2. 点击右上角头像 → Settings
3. 左侧菜单选择 "Access Tokens"
4. 创建新的令牌，权限选择：
   - `api` - 完整的 API 访问权限
   - `read_user` - 读取用户信息
   - `read_repository` - 读取仓库
   - `write_repository` - 写入仓库

⚠️ **重要**: 保存好生成的令牌，它只会显示一次！

### 2. 系统依赖

确保系统安装了以下工具：

```bash
# Ubuntu/Debian
sudo apt-get install git curl jq python3 python3-pip

# macOS
brew install git curl jq python3

# CentOS/RHEL
sudo yum install git curl jq python3 python3-pip
```

## 🚀 快速部署

### 方法一：一键部署脚本

```bash
# 进入项目目录
cd github-actions-ssh

# 设置环境变量
export GITLAB_USERNAME="your-username"
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"

# 执行一键部署
./scripts/upload-to-gitlab.sh --generate-pdf --init-repo --setup-pages
```

### 方法二：分步部署

#### 步骤 1: 安装 PDF 生成依赖

```bash
./scripts/install-dependencies.sh
```

#### 步骤 2: 生成 PDF 文档

```bash
# 使用 Makefile
make pdf-compress

# 或直接使用脚本
./scripts/batch-generate-pdf.sh -c -i . output
```

#### 步骤 3: 上传到 GitLab

```bash
./scripts/upload-to-gitlab.sh \
  -u your-username \
  -t glpat-xxxxxxxxxxxxxxxxxxxx \
  --init-repo \
  --setup-pages
```

## 📖 详细配置

### GitLab CI/CD 配置

项目包含完整的 `.gitlab-ci.yml` 配置文件，支持：

- 🔧 **自动依赖安装**
- 📄 **PDF 文档生成**
- 🧪 **文档质量测试**
- 🌐 **GitLab Pages 部署**
- 📦 **自动发布创建**

### 环境变量设置

在 GitLab 项目中设置以下 CI/CD 变量：

| 变量名 | 描述 | 必需 |
|--------|------|------|
| `GITLAB_USERNAME` | GitLab 用户名 | ✅ |
| `GITLAB_TOKEN` | GitLab 访问令牌 | ✅ |

### Pages 配置

GitLab Pages 会自动配置，访问地址为：
- `https://your-username.gitlab.io/github-actions-ssh-guide`

## 📁 项目结构

部署后的项目结构：

```
github-actions-ssh-guide/
├── 📄 README.md                    # 主要文档
├── 🔧 .gitlab-ci.yml               # GitLab CI/CD 配置
├── 📦 requirements.txt             # Python 依赖
├── 🛠️ Makefile                    # 构建工具
├── 📁 scripts/                    # 脚本目录
│   ├── generate-pdf.py            # PDF 生成器
│   ├── batch-generate-pdf.sh      # 批量生成脚本
│   ├── install-dependencies.sh    # 依赖安装脚本
│   └── upload-to-gitlab.sh        # GitLab 上传脚本
├── 📁 .github/workflows/          # GitHub Actions 示例
│   ├── basic-ssh.yml              # 基础 SSH 连接
│   ├── deploy-with-ssh.yml        # 完整部署示例
│   ├── multi-server-deploy.yml    # 多服务器部署
│   └── database-backup.yml        # 数据库备份
└── 📁 public/                     # 生成的文档
    ├── index.html                 # 文档索引页面
    ├── 📁 pdfs/                   # PDF 文档
    └── 📁 html/                   # HTML 文档
```

## 🔍 验证部署

### 1. 检查 CI/CD 管道

1. 访问 GitLab 项目页面
2. 点击 "CI/CD" → "Pipelines"
3. 查看最新的管道执行状态

### 2. 验证 Pages 部署

1. 访问 `https://your-username.gitlab.io/github-actions-ssh-guide`
2. 检查文档索引页面是否正常显示
3. 下载 PDF 文档测试

### 3. 测试 PDF 生成

```bash
# 手动测试 PDF 生成
python3 scripts/generate-pdf.py README.md -o test.pdf

# 检查生成的文件
ls -la test.pdf
```

## 🛠️ 故障排除

### 常见问题

#### 1. 权限错误

**问题**: `Permission denied (publickey)`

**解决方案**:
```bash
# 检查 SSH 密钥
ssh -T git@gitlab.com

# 或使用 HTTPS
git remote set-url origin https://gitlab.com/username/repo.git
```

#### 2. PDF 生成失败

**问题**: `ModuleNotFoundError: No module named 'weasyprint'`

**解决方案**:
```bash
# 重新安装依赖
./scripts/install-dependencies.sh --python-only

# 或手动安装
pip3 install -r requirements.txt
```

#### 3. GitLab API 错误

**问题**: `401 Unauthorized`

**解决方案**:
- 检查访问令牌是否正确
- 确认令牌权限包含 `api`
- 验证用户名是否正确

#### 4. Pages 部署失败

**问题**: Pages 无法访问

**解决方案**:
1. 检查 `.gitlab-ci.yml` 中的 `pages` 作业
2. 确认 `public` 目录包含 `index.html`
3. 检查项目设置中的 Pages 配置

### 调试技巧

#### 1. 启用详细日志

```bash
# 设置调试模式
export DEBUG=1
./scripts/upload-to-gitlab.sh --generate-pdf
```

#### 2. 检查 CI/CD 日志

1. 进入 GitLab 项目
2. CI/CD → Pipelines
3. 点击具体的作业查看日志

#### 3. 本地测试

```bash
# 测试 PDF 生成
make test

# 测试完整流程
make all

# 检查项目状态
make status
```

## 🔄 自动化工作流

### 触发条件

GitLab CI/CD 会在以下情况自动运行：

1. **推送到 main 分支** - 完整构建和部署
2. **创建 Merge Request** - 构建和测试
3. **创建标签** - 创建发布版本
4. **手动触发** - 可以手动运行任何作业

### 管道阶段

1. **Install** - 安装依赖
2. **Build** - 生成 PDF 和 HTML
3. **Test** - 验证生成的文档
4. **Deploy** - 部署到 GitLab Pages
5. **Release** - 创建发布版本（手动）

## 📊 监控和维护

### 定期任务

建议设置以下定期任务：

1. **每周检查** - 验证 Pages 是否正常访问
2. **每月更新** - 更新依赖包版本
3. **季度审查** - 检查文档内容是否需要更新

### 性能优化

```bash
# 清理旧的构建缓存
make clean-all

# 压缩 PDF 文件
make pdf-compress

# 检查文件大小
make info
```

## 🎯 最佳实践

### 1. 版本管理

- 使用语义化版本标签 (v1.0.0, v1.1.0)
- 定期创建发布版本
- 保持清晰的提交信息

### 2. 文档维护

- 定期更新 README.md
- 保持示例代码的时效性
- 添加新功能的使用说明

### 3. 安全考虑

- 定期轮换访问令牌
- 使用最小权限原则
- 监控仓库访问日志

## 📞 支持和反馈

如果在部署过程中遇到问题：

1. 📖 查看本文档的故障排除部分
2. 🔍 检查 GitLab CI/CD 日志
3. 🐛 在项目中创建 Issue
4. 💬 联系项目维护者

## 🎉 部署完成

恭喜！您已经成功将 GitHub Actions SSH 使用指南部署到 GitLab。

现在您可以：

- ✅ 访问在线文档
- ✅ 下载 PDF 版本
- ✅ 自动化文档更新
- ✅ 与团队共享知识

访问您的文档：`https://your-username.gitlab.io/github-actions-ssh-guide`