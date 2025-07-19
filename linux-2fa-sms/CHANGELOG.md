# 📋 变更日志

所有对该项目的重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且此项目遵循 [语义化版本控制](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划中的功能
- TOTP (Time-based One-Time Password) 支持
- Web 管理界面
- 多语言支持
- Docker 容器化部署
- 邮件验证码支持

## [1.0.0] - 2024-01-01

### 🎉 新增
- **核心功能**
  - 基于阿里云短信服务的双重因子认证系统
  - 完整的 PAM 集成支持
  - 密码 + 短信验证码双重保护机制
  
- **安全特性**
  - 验证码时效性控制 (默认5分钟)
  - 暴力破解防护 (失败次数和时间锁定)
  - 重放攻击防护 (验证码一次性使用)
  - 完整的审计日志记录
  - 敏感配置信息加密存储
  - 用户绕过机制支持

- **核心模块**
  - `aliyun_sms.py` - 阿里云短信 API 集成
  - `sms_2fa.py` - 双重认证器核心逻辑
  - `pam_sms_2fa.py` - PAM 认证模块
  - `config.py` - 配置管理系统

- **管理工具**
  - `install.sh` - 一键安装脚本
  - `user_manager.py` - 用户管理工具
  - `test_sms.py` - 短信测试工具

- **系统集成**
  - systemd 服务支持
  - 日志轮转配置
  - Redis 缓存支持 (可选)
  - 多平台兼容性 (Ubuntu/CentOS/Fedora/openSUSE)

- **文档**
  - 详细的安装配置指南
  - 使用示例和最佳实践
  - 故障排除说明
  - API 文档和配置说明
  - 贡献指南

### 🛠️ 技术实现
- Python 3.7+ 支持
- 阿里云短信 SDK 集成
- PAM (Pluggable Authentication Modules) 集成
- 配置文件加密存储
- 结构化日志记录
- 异常处理和错误恢复

### 📊 性能特性
- 验证码生成优化
- 短信发送频率限制
- 内存缓存和 Redis 缓存支持
- 异步日志写入
- 连接池优化

### 🔧 配置选项
- 阿里云短信服务配置
- 验证码长度和过期时间
- 安全策略配置
- PAM 集成选项
- 审计日志配置

### ✅ 测试覆盖
- 单元测试覆盖主要模块
- 集成测试验证 PAM 集成
- 性能测试和压力测试
- 安全测试和渗透测试

## [0.9.0] - 2023-12-15

### 🧪 Beta 版本
- 初始 Beta 版本发布
- 核心功能基本完成
- 内部测试和验证

## [0.1.0] - 2023-11-01

### 🚀 项目启动
- 项目初始化
- 基础架构设计
- 技术选型确定

---

## 版本说明

### 版本号格式
使用 `MAJOR.MINOR.PATCH` 格式：
- **MAJOR**: 不兼容的API修改
- **MINOR**: 向下兼容的功能性新增
- **PATCH**: 向下兼容的问题修正

### 标签说明
- 🎉 新增 (Added) - 新功能
- 🛠️ 更改 (Changed) - 对现有功能的变更
- 🔧 修复 (Fixed) - 任何bug修复
- 🗑️ 移除 (Removed) - 现在移除的功能
- 🚨 废弃 (Deprecated) - 稍后会被移除的特性
- 🔒 安全 (Security) - 安全相关的修复

### 链接格式
- [Unreleased]: https://github.com/your-repo/linux-sms-2fa/compare/v1.0.0...HEAD
- [1.0.0]: https://github.com/your-repo/linux-sms-2fa/releases/tag/v1.0.0
- [0.9.0]: https://github.com/your-repo/linux-sms-2fa/releases/tag/v0.9.0
- [0.1.0]: https://github.com/your-repo/linux-sms-2fa/releases/tag/v0.1.0