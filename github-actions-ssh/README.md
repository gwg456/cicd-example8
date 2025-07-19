# GitHub Actions SSH 使用指南

## 📋 目录
1. [SSH 密钥生成和配置](#ssh-密钥生成和配置)
2. [GitHub Secrets 配置](#github-secrets-配置)
3. [基础 SSH 连接示例](#基础-ssh-连接示例)
4. [完整部署示例](#完整部署示例)
5. [多服务器部署](#多服务器部署)
6. [安全最佳实践](#安全最佳实践)

## 🔑 SSH 密钥生成和配置

### 1. 生成 SSH 密钥对
```bash
# 在本地机器生成 SSH 密钥对
ssh-keygen -t rsa -b 4096 -C "github-actions@yourdomain.com" -f ~/.ssh/github_actions_rsa

# 或使用 ed25519 (推荐，更安全)
ssh-keygen -t ed25519 -C "github-actions@yourdomain.com" -f ~/.ssh/github_actions_ed25519
```

### 2. 将公钥添加到服务器
```bash
# 复制公钥到服务器
ssh-copy-id -i ~/.ssh/github_actions_rsa.pub user@your-server.com

# 或手动添加
cat ~/.ssh/github_actions_rsa.pub | ssh user@your-server.com "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 3. 测试 SSH 连接
```bash
# 测试连接
ssh -i ~/.ssh/github_actions_rsa user@your-server.com

# 测试无密码登录
ssh -o PasswordAuthentication=no -i ~/.ssh/github_actions_rsa user@your-server.com
```

## 🔒 GitHub Secrets 配置

在 GitHub 仓库中设置以下 Secrets：

### 必需的 Secrets
- `SSH_PRIVATE_KEY`: SSH 私钥内容
- `SSH_HOST`: 服务器 IP 或域名
- `SSH_USERNAME`: SSH 用户名
- `SSH_PORT`: SSH 端口 (默认 22)

### 可选的 Secrets
- `SSH_PASSWORD`: SSH 密码 (仅在需要时使用)
- `SSH_PASSPHRASE`: 私钥密码短语
- `KNOWN_HOSTS`: 服务器指纹信息

### 设置步骤
1. 进入 GitHub 仓库
2. Settings → Secrets and variables → Actions
3. 点击 "New repository secret"
4. 添加上述密钥

## 📖 使用示例

### 基础示例
参见 `.github/workflows/` 目录下的示例文件：
- `basic-ssh.yml` - 基础 SSH 连接
- `deploy-with-ssh.yml` - 完整部署流程
- `multi-server-deploy.yml` - 多服务器部署
- `docker-deploy.yml` - Docker 应用部署
- `database-backup.yml` - 数据库备份

### 常用 SSH Actions
1. **appleboy/ssh-action** - 最流行的 SSH Action
2. **shimataro/ssh-key-action** - SSH 密钥管理
3. **burnett01/rsync-deployments** - 文件同步部署

## 🛡️ 安全最佳实践

1. **使用专用的部署密钥**
2. **限制服务器用户权限**
3. **使用堡垒机/跳板机**
4. **定期轮换密钥**
5. **监控 SSH 连接日志**
6. **使用 known_hosts 验证服务器身份**

## 🔧 故障排除

### 常见问题
1. **Permission denied (publickey)** - 检查密钥配置
2. **Host key verification failed** - 配置 known_hosts
3. **Connection timeout** - 检查防火墙和网络
4. **Command not found** - 检查 PATH 环境变量

### 调试技巧
- 使用 `ssh -v` 增加详细输出
- 检查服务器 `/var/log/auth.log`
- 验证密钥文件权限 (600)
- 确认 `.ssh` 目录权限 (700)