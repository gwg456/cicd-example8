# 🔐 Linux 服务器双重因子登录解决方案

基于阿里云短信服务的 Linux 服务器双重因子认证系统，实现密码 + 短信验证码的安全登录机制。

## 📋 功能特性

- 🔑 **密码认证** + 📱 **短信验证码** 双重保护
- ☁️ 基于阿里云短信服务的可靠性保障
- 🛡️ 支持多种 PAM 集成方式
- 📊 完整的审计日志记录
- ⚙️ 灵活的配置管理
- 🚀 简单易部署的安装脚本

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户登录      │───▶│   PAM 认证      │───▶│   2FA 验证      │
│   (SSH/TTY)     │    │   (密码验证)    │    │   (短信验证码)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   登录成功      │◀───│   验证通过      │◀───│   阿里云短信    │
│                 │    │                 │    │   服务 API      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 项目结构

```
linux-2fa-sms/
├── 📄 README.md                    # 项目说明
├── 📄 requirements.txt             # Python 依赖
├── 📁 src/                        # 源代码
│   ├── sms_2fa.py                 # 主要 2FA 模块
│   ├── aliyun_sms.py              # 阿里云短信接口
│   ├── pam_2fa.py                 # PAM 认证模块
│   └── config.py                  # 配置管理
├── 📁 config/                     # 配置文件
│   ├── 2fa.conf                   # 主配置文件
│   └── users.conf                 # 用户配置
├── 📁 scripts/                    # 安装和管理脚本
│   ├── install.sh                 # 安装脚本
│   ├── setup_pam.sh               # PAM 配置脚本
│   ├── user_manager.py            # 用户管理工具
│   └── test_sms.py                # 短信测试工具
├── 📁 systemd/                    # 系统服务
│   └── sms-2fa.service            # systemd 服务文件
├── 📁 pam/                        # PAM 模块
│   └── pam_sms_2fa.py             # PAM 模块实现
├── 📁 logs/                       # 日志目录
└── 📁 docs/                       # 文档目录
    ├── installation.md            # 安装指南
    ├── configuration.md           # 配置说明
    └── troubleshooting.md         # 故障排除
```

## 🚀 快速开始

### 1. 准备阿里云短信服务

1. 登录阿里云控制台
2. 开通短信服务
3. 创建签名和模板
4. 获取 AccessKey ID 和 AccessKey Secret

### 2. 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-repo/linux-2fa-sms.git
cd linux-2fa-sms

# 安装系统依赖
sudo apt-get update
sudo apt-get install python3 python3-pip libpam-python

# 安装 Python 依赖
pip3 install -r requirements.txt
```

### 3. 配置系统

```bash
# 运行安装脚本
sudo ./scripts/install.sh

# 配置 PAM
sudo ./scripts/setup_pam.sh

# 编辑配置文件
sudo nano /etc/sms-2fa/2fa.conf
```

### 4. 测试系统

```bash
# 测试短信发送
python3 scripts/test_sms.py +8613812345678

# 测试用户认证
sudo python3 scripts/test_auth.py username
```

## ⚙️ 配置说明

### 阿里云短信配置

在 `/etc/sms-2fa/2fa.conf` 中配置：

```ini
[aliyun]
access_key_id = YOUR_ACCESS_KEY_ID
access_key_secret = YOUR_ACCESS_KEY_SECRET
region = cn-hangzhou
sign_name = 您的签名
template_code = SMS_123456789
```

### 用户手机号配置

在 `/etc/sms-2fa/users.conf` 中配置：

```ini
[users]
username1 = +8613812345678
username2 = +8613987654321
admin = +8618888888888
```

## 🔧 使用方法

### SSH 登录流程

1. 用户使用 SSH 连接服务器
2. 输入用户名和密码（第一重认证）
3. 系统发送短信验证码到用户手机
4. 用户输入收到的验证码（第二重认证）
5. 验证通过，登录成功

### 管理用户

```bash
# 添加用户
sudo python3 scripts/user_manager.py add username +8613812345678

# 删除用户
sudo python3 scripts/user_manager.py remove username

# 列出用户
sudo python3 scripts/user_manager.py list

# 测试用户手机号
sudo python3 scripts/user_manager.py test username
```

## 📱 短信模板示例

推荐的阿里云短信模板：

```
您的验证码是：${code}，有效期5分钟，请勿泄露给他人。
```

变量：
- `code`: 6位数字验证码

## 🛡️ 安全特性

- ✅ **验证码时效性** - 5分钟有效期
- ✅ **重放攻击防护** - 验证码一次性使用
- ✅ **暴力破解防护** - 失败次数限制
- ✅ **审计日志** - 完整的认证日志记录
- ✅ **加密存储** - 敏感信息加密保存

## 📊 监控和日志

### 日志位置

- 认证日志: `/var/log/sms-2fa/auth.log`
- 短信日志: `/var/log/sms-2fa/sms.log`
- 错误日志: `/var/log/sms-2fa/error.log`

### 监控指标

- 登录成功/失败率
- 短信发送成功率
- 验证码验证通过率
- 用户登录频次

## 🔍 故障排除

### 常见问题

1. **短信发送失败**
   - 检查阿里云配置
   - 验证手机号格式
   - 查看短信余额

2. **PAM 认证失败**
   - 检查 PAM 配置
   - 验证模块权限
   - 查看系统日志

3. **验证码过期**
   - 调整有效期配置
   - 检查系统时间
   - 重新发送验证码

## 📈 性能优化

- 🚀 **缓存机制** - Redis 缓存验证码
- 🔄 **连接池** - HTTP 连接复用
- 📦 **批量处理** - 多用户批量验证
- 🎯 **负载均衡** - 多区域短信发送

## 🔒 安全建议

1. **定期轮换密钥** - 定期更新 AccessKey
2. **网络隔离** - 限制 API 访问来源
3. **监控告警** - 异常登录行为告警
4. **备份恢复** - 定期备份配置文件

## 📞 支持与反馈

- 📖 [详细文档](docs/)
- 🐛 [问题反馈](https://github.com/your-repo/issues)
- 💬 [讨论交流](https://github.com/your-repo/discussions)

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件