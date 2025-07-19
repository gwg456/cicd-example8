# 🔐 Git推送权限配置指南

## ❌ 权限不足问题分析

当出现以下错误时：
```
remote: Permission to samples28/ggggg.git denied to cursor[bot].
fatal: unable to access 'https://github.com/samples28/ggggg.git/': The requested URL returned error: 403
```

说明当前使用的认证方式没有推送权限。

## 🛠️ 解决方案

### 方案1: 使用个人访问令牌 (Personal Access Token)

#### 1️⃣ 创建GitHub个人访问令牌
1. 登录GitHub → 点击头像 → Settings
2. 左侧菜单 → Developer settings → Personal access tokens → Tokens (classic)
3. 点击 "Generate new token" → "Generate new token (classic)"
4. 设置令牌信息：
   - **Note**: `Linux SMS 2FA Project`
   - **Expiration**: 选择过期时间
   - **Scopes**: 勾选以下权限
     - ✅ `repo` (完整仓库访问权限)
     - ✅ `workflow` (GitHub Actions权限)
5. 点击 "Generate token"
6. **重要**: 复制生成的token，它只显示一次

#### 2️⃣ 使用令牌推送
```bash
# 方法1: 在URL中包含令牌
git remote set-url origin https://YOUR_TOKEN@github.com/samples28/ggggg.git
git push -u origin main
git push origin --tags

# 方法2: 使用Git凭据管理器
git config --global credential.helper store
git push -u origin main
# 输入用户名: samples28
# 输入密码: YOUR_TOKEN (不是GitHub密码)
```

### 方案2: 配置SSH密钥认证

#### 1️⃣ 生成SSH密钥
```bash
# 生成新的SSH密钥
ssh-keygen -t ed25519 -C "your.email@example.com"
# 或者使用RSA格式
ssh-keygen -t rsa -b 4096 -C "your.email@example.com"

# 启动ssh-agent
eval "$(ssh-agent -s)"

# 添加SSH密钥到ssh-agent
ssh-add ~/.ssh/id_ed25519
```

#### 2️⃣ 添加SSH公钥到GitHub
1. 复制SSH公钥到剪贴板：
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
2. 登录GitHub → Settings → SSH and GPG keys
3. 点击 "New SSH key"
4. 粘贴公钥内容，设置标题
5. 点击 "Add SSH key"

#### 3️⃣ 使用SSH URL推送
```bash
# 更改远程URL为SSH格式
git remote set-url origin git@github.com:samples28/ggggg.git

# 测试SSH连接
ssh -T git@github.com

# 推送代码
git push -u origin main
git push origin --tags
```

### 方案3: 使用GitHub CLI

#### 1️⃣ 安装GitHub CLI
```bash
# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# macOS
brew install gh

# Windows
winget install --id GitHub.cli
```

#### 2️⃣ 认证和推送
```bash
# 登录GitHub
gh auth login

# 推送代码
git push -u origin main
git push origin --tags
```

### 方案4: 检查仓库权限设置

#### 1️⃣ 确认仓库权限
- 确保您是仓库的**所有者**或**协作者**
- 检查仓库是否为**私有仓库**需要相应权限

#### 2️⃣ 添加协作者权限
1. 仓库所有者操作：
2. 进入仓库 → Settings → Manage access
3. 点击 "Invite a collaborator"
4. 输入用户名并发送邀请
5. 被邀请者接受邀请

## 🚀 完整推送脚本

创建 `secure_push.sh` 脚本：

```bash
#!/bin/bash
# 安全推送脚本

echo "🔐 Linux SMS 2FA 安全推送脚本"
echo "================================"

# 检查当前认证状态
echo "📋 检查Git配置..."
echo "用户名: $(git config user.name)"
echo "邮箱: $(git config user.email)"
echo "远程仓库: $(git remote get-url origin)"
echo ""

# 选择认证方式
echo "请选择认证方式:"
echo "1) 个人访问令牌 (HTTPS)"
echo "2) SSH密钥"
echo "3) GitHub CLI"
read -p "请输入选择 (1-3): " auth_method

case $auth_method in
    1)
        read -p "请输入您的GitHub个人访问令牌: " token
        git remote set-url origin https://$token@github.com/samples28/ggggg.git
        ;;
    2)
        git remote set-url origin git@github.com:samples28/ggggg.git
        echo "请确保SSH密钥已配置"
        ;;
    3)
        gh auth status || gh auth login
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

# 推送代码
echo "🚀 开始推送..."
if git push -u origin main; then
    echo "✅ 主分支推送成功"
    if git push origin --tags; then
        echo "✅ 标签推送成功"
    else
        echo "⚠️ 标签推送失败"
    fi
else
    echo "❌ 推送失败，请检查权限设置"
    exit 1
fi

echo "🎉 推送完成！"
echo "📍 仓库地址: https://github.com/samples28/ggggg"
```

## 📋 权限检查清单

在推送前，请确认：

- [ ] 您有仓库的写入权限
- [ ] 仓库存在且可访问
- [ ] Git配置正确（用户名和邮箱）
- [ ] 认证方式已正确配置
- [ ] 网络连接正常
- [ ] 防火墙未阻止Git操作

## 🆘 常见问题排查

### 问题1: "repository not found"
```bash
# 检查仓库URL是否正确
git remote -v

# 确认仓库是否存在
curl -I https://github.com/samples28/ggggg
```

### 问题2: "authentication failed"
```bash
# 清除Git凭据缓存
git config --global --unset credential.helper
git config --system --unset credential.helper

# 重新设置认证
git config --global credential.helper store
```

### 问题3: SSH连接问题
```bash
# 测试SSH连接
ssh -T git@github.com -v

# 检查SSH配置
cat ~/.ssh/config
```

## 🔧 快速修复命令

```bash
# 快速修复脚本
#!/bin/bash
echo "🔧 快速修复Git推送权限..."

# 重置远程URL
git remote remove origin
git remote add origin https://github.com/samples28/ggggg.git

# 配置Git用户信息
read -p "输入GitHub用户名: " username
read -p "输入GitHub邮箱: " email
git config user.name "$username"
git config user.email "$email"

# 使用令牌推送
read -p "输入Personal Access Token: " token
git remote set-url origin https://$token@github.com/samples28/ggggg.git

echo "✅ 配置完成，现在可以推送了："
echo "git push -u origin main"
echo "git push origin --tags"
```

选择最适合您的认证方式，配置完成后即可成功推送项目！