# OIDC (OpenID Connect) 设置指南

## 概述

本文档介绍如何在 User Auth API 中配置和使用 OIDC (OpenID Connect) 认证。支持多种 OIDC 提供商，包括 Google、Microsoft Azure AD、GitHub 等。

## 🔧 支持的 OIDC 提供商

1. **Google OAuth 2.0 / OIDC**
2. **Microsoft Azure AD**
3. **GitHub OAuth 2.0**
4. **自定义 OIDC 提供商**

## 📋 环境变量配置

### 基础配置

```bash
# 应用基础URL
BASE_URL=http://localhost:8000

# OIDC相关设置
OIDC_AUTO_REGISTER=true          # 是否自动注册OIDC用户
OIDC_UPDATE_USER_INFO=true       # 是否更新用户信息

# Session设置
SESSION_SECRET_KEY=your-session-secret-key
SESSION_MAX_AGE=3600             # 1小时
```

### Google OIDC 配置

1. **创建 Google OAuth 应用**：
   - 访问 [Google Cloud Console](https://console.cloud.google.com/)
   - 创建新项目或选择现有项目
   - 启用 Google+ API
   - 创建 OAuth 2.0 凭据

2. **环境变量**：
```bash
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

3. **回调URL设置**：
   - 授权重定向 URI: `http://localhost:8000/api/v1/auth/oidc/callback/google`

### Microsoft Azure AD 配置

1. **创建 Azure AD 应用**：
   - 访问 [Azure Portal](https://portal.azure.com/)
   - 进入 Azure Active Directory
   - 创建应用注册

2. **环境变量**：
```bash
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-tenant-id                # 可选，默认为 "common"
```

3. **回调URL设置**：
   - 重定向 URI: `http://localhost:8000/api/v1/auth/oidc/callback/azure`

### GitHub OAuth 配置

1. **创建 GitHub OAuth 应用**：
   - 访问 GitHub Settings > Developer settings > OAuth Apps
   - 创建新的 OAuth App

2. **环境变量**：
```bash
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

3. **回调URL设置**：
   - Authorization callback URL: `http://localhost:8000/api/v1/auth/oidc/callback/github`

### 自定义 OIDC 提供商配置

对于支持标准 OIDC 的其他提供商：

```bash
CUSTOM_OIDC_NAME=Your Provider Name
CUSTOM_OIDC_CLIENT_ID=your-client-id
CUSTOM_OIDC_CLIENT_SECRET=your-client-secret
CUSTOM_OIDC_DISCOVERY_URL=https://your-provider.com/.well-known/openid_configuration
CUSTOM_OIDC_SCOPES=["openid", "profile", "email"]
```

## 🚀 使用流程

### 1. 获取可用提供商

```bash
GET /api/v1/auth/oidc/providers
```

响应示例：
```json
{
  "providers": [
    {
      "name": "google",
      "display_name": "Google",
      "login_url": "/api/v1/auth/oidc/login/google"
    },
    {
      "name": "azure",
      "display_name": "Microsoft",
      "login_url": "/api/v1/auth/oidc/login/azure"
    }
  ],
  "count": 2
}
```

### 2. 启动 OIDC 登录

用户点击登录链接或访问：
```bash
GET /api/v1/auth/oidc/login/{provider_name}
```

这会重定向用户到对应的 OIDC 提供商进行认证。

### 3. 处理回调

OIDC 提供商认证成功后，会重定向到：
```bash
GET /api/v1/auth/oidc/callback/{provider_name}?code=xxx&state=xxx
```

成功响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "provider": "google"
  }
}
```

### 4. 使用访问令牌

使用返回的 JWT token 访问受保护的 API：
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer your-jwt-token"
```

### 5. 注销 (可选)

启动 OIDC 提供商注销：
```bash
POST /api/v1/auth/oidc/logout/{provider_name}
```

可选参数：
```json
{
  "id_token_hint": "your-id-token"
}
```

## 🔒 安全特性

### 1. PKCE (Proof Key for Code Exchange)
- 自动为支持的提供商启用 PKCE
- 增强 OAuth 2.0 授权码流的安全性

### 2. State 参数验证
- 防止 CSRF 攻击
- 每次认证会话使用唯一的 state 参数

### 3. Nonce 验证
- 用于 ID Token 验证
- 防止重放攻击

### 4. ID Token 验证
- 验证 ID Token 的签名和声明
- 确保 token 的完整性和真实性

## 📊 数据库架构

### 用户表更新
```sql
ALTER TABLE users ADD COLUMN is_oidc_user BOOLEAN DEFAULT FALSE;
ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;
```

### OIDC 链接表
```sql
CREATE TABLE user_oidc_links (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    provider VARCHAR NOT NULL,
    provider_user_id VARCHAR NOT NULL,
    provider_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(provider, provider_user_id)
);
```

## 🔄 用户账户管理

### 自动注册
当 `OIDC_AUTO_REGISTER=true` 时：
- 新的 OIDC 用户会自动创建账户
- 用户名从邮箱或显示名称生成
- 确保用户名唯一性

### 账户链接
- 支持同一用户链接多个 OIDC 提供商
- 通过邮箱地址检测重复账户
- 可配置账户合并策略

### 信息更新
当 `OIDC_UPDATE_USER_INFO=true` 时：
- 每次登录时更新用户信息
- 同步显示名称和邮箱地址

## 🛠️ 开发和测试

### 本地开发设置

1. **设置环境变量**：
```bash
cp .env.example .env
# 编辑 .env 文件，添加你的 OIDC 配置
```

2. **运行数据库迁移**：
```bash
alembic upgrade head
```

3. **启动应用**：
```bash
uvicorn app.main:app --reload
```

4. **测试 OIDC 流程**：
   - 访问 `http://localhost:8000/docs`
   - 使用 `/api/v1/auth/oidc/providers` 端点

### 测试用例

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_oidc_providers():
    response = client.get("/api/v1/auth/oidc/providers")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert isinstance(data["providers"], list)

def test_oidc_login_redirect():
    response = client.get("/api/v1/auth/oidc/login/google", follow_redirects=False)
    assert response.status_code == 302
    assert "accounts.google.com" in response.headers["location"]
```

## 🚨 故障排除

### 常见问题

1. **"Provider not found" 错误**
   - 检查环境变量是否正确设置
   - 确认 CLIENT_ID 和 CLIENT_SECRET 已配置

2. **回调URL不匹配**
   - 检查 OIDC 提供商的回调URL配置
   - 确认 BASE_URL 环境变量正确

3. **ID Token 验证失败**
   - 检查系统时间是否准确
   - 验证 OIDC 提供商的时钟偏差设置

4. **Session 丢失**
   - 检查 SESSION_SECRET_KEY 设置
   - 确认 cookie 设置正确

### 调试技巧

1. **启用详细日志**：
```python
import logging
logging.getLogger("app.oidc_service").setLevel(logging.DEBUG)
```

2. **查看原始响应**：
```python
# 在 oidc_service.py 中添加调试输出
print(f"Discovery document: {discovery_doc}")
print(f"User info response: {user_info}")
```

## 📚 相关文档

- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
- [FastAPI OAuth2 文档](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

## 🔮 未来计划

- [ ] 支持 SAML 2.0 认证
- [ ] 实现 token 刷新机制
- [ ] 添加多因素认证 (MFA)
- [ ] 支持企业级单点登录 (SSO)
- [ ] 实现会话管理和并发控制