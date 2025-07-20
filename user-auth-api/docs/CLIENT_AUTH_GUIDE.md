# 客户端认证指南

## 概述

本API现在支持多种认证方式，专为外部客户端（移动应用、桌面应用、其他API服务）设计。不再需要Web重定向，支持纯API交互。

## 🔑 支持的认证方式

1. **用户JWT认证** - 传统的用户登录认证
2. **客户端凭据流** - OAuth 2.0 Client Credentials Grant
3. **API密钥认证** - 基于API Key的认证
4. **OIDC认证** - 第三方身份提供商（保留支持）

## 🚀 客户端凭据流 (Client Credentials Flow)

### 1. 注册API客户端

首先需要通过用户账户注册API客户端：

```bash
# 用户登录获取JWT
curl -X POST "http://localhost:8000/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'

# 使用JWT注册客户端
curl -X POST "http://localhost:8000/api/v1/client/register" \
  -H "Authorization: Bearer YOUR_USER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Mobile App",
    "description": "iOS/Android mobile application",
    "scopes": ["read", "write"],
    "is_trusted": false,
    "expires_days": 365
  }'
```

**响应示例：**
```json
{
  "id": 1,
  "client_id": "client_abc123def456",
  "client_secret": "secret_xyz789uvw012",
  "name": "My Mobile App",
  "description": "iOS/Android mobile application",
  "scopes": ["read", "write"],
  "is_active": true,
  "is_trusted": false,
  "owner_id": 1,
  "created_at": "2024-01-01T10:00:00Z",
  "expires_at": "2025-01-01T10:00:00Z"
}
```

> ⚠️ **重要**：`client_secret` 只在创建时返回一次，请妥善保存！

### 2. 获取客户端访问令牌

```bash
curl -X POST "http://localhost:8000/api/v1/client/token" \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "client_abc123def456",
    "client_secret": "secret_xyz789uvw012",
    "scope": "read write"
  }'
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "scope": "read write"
}
```

### 3. 使用客户端令牌访问API

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 🗝️ API密钥认证

### 1. 为客户端创建API密钥

```bash
curl -X POST "http://localhost:8000/api/v1/client/client_abc123def456/keys" \
  -H "Authorization: Bearer YOUR_USER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "scopes": ["read"],
    "expires_days": 30
  }'
```

**响应：**
```json
{
  "id": 1,
  "key_id": "ak_1_64",
  "key_value": "ak_1234567890abcdef1234567890abcdef",
  "name": "Production API Key",
  "scopes": ["read"],
  "is_active": true,
  "expires_at": "2024-02-01T10:00:00Z"
}
```

### 2. 使用API密钥访问

#### 方式一：简单API密钥（开发环境）

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "X-API-Key: ak_1234567890abcdef1234567890abcdef"
```

#### 方式二：签名API密钥（生产环境推荐）

```bash
# 计算签名
timestamp=$(date +%s)
api_key="ak_1234567890abcdef1234567890abcdef"
client_secret="secret_xyz789uvw012"
string_to_sign="${api_key}:${timestamp}"
signature=$(echo -n "$string_to_sign" | openssl dgst -sha256 -hmac "$client_secret" -binary | base64)

curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "X-API-Key: $api_key" \
  -H "X-API-Timestamp: $timestamp" \
  -H "X-API-Signature: $signature"
```

## 📱 客户端应用示例

### Python客户端示例

```python
import requests
import time
import hmac
import hashlib
import base64

class APIClient:
    def __init__(self, base_url, client_id, client_secret):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
    
    def get_client_token(self):
        """获取客户端访问令牌"""
        response = requests.post(f"{self.base_url}/api/v1/client/token", json={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "read write"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            return self.access_token
        else:
            raise Exception(f"Failed to get token: {response.text}")
    
    def api_request(self, method, endpoint, **kwargs):
        """使用客户端令牌发送API请求"""
        if not self.access_token:
            self.get_client_token()
        
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f"Bearer {self.access_token}"
        
        response = requests.request(
            method, 
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )
        
        # 如果token过期，重新获取
        if response.status_code == 401:
            self.get_client_token()
            headers['Authorization'] = f"Bearer {self.access_token}"
            response = requests.request(
                method, 
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            )
        
        return response

# 使用示例
client = APIClient(
    base_url="http://localhost:8000",
    client_id="client_abc123def456",
    client_secret="secret_xyz789uvw012"
)

# 获取用户信息
response = client.api_request('GET', '/api/v1/users/me')
print(response.json())
```

### JavaScript/Node.js客户端示例

```javascript
const crypto = require('crypto');

class APIClient {
    constructor(baseUrl, clientId, clientSecret) {
        this.baseUrl = baseUrl;
        this.clientId = clientId;
        this.clientSecret = clientSecret;
        this.accessToken = null;
    }
    
    async getClientToken() {
        const response = await fetch(`${this.baseUrl}/api/v1/client/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grant_type: 'client_credentials',
                client_id: this.clientId,
                client_secret: this.clientSecret,
                scope: 'read write'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.access_token;
            return this.accessToken;
        } else {
            throw new Error(`Failed to get token: ${await response.text()}`);
        }
    }
    
    async apiRequest(method, endpoint, options = {}) {
        if (!this.accessToken) {
            await this.getClientToken();
        }
        
        const headers = {
            'Authorization': `Bearer ${this.accessToken}`,
            ...options.headers
        };
        
        let response = await fetch(`${this.baseUrl}${endpoint}`, {
            method,
            headers,
            ...options
        });
        
        // 如果token过期，重新获取
        if (response.status === 401) {
            await this.getClientToken();
            headers['Authorization'] = `Bearer ${this.accessToken}`;
            response = await fetch(`${this.baseUrl}${endpoint}`, {
                method,
                headers,
                ...options
            });
        }
        
        return response;
    }
}

// 使用示例
const client = new APIClient(
    'http://localhost:8000',
    'client_abc123def456',
    'secret_xyz789uvw012'
);

// 获取用户信息
client.apiRequest('GET', '/api/v1/users/me')
    .then(response => response.json())
    .then(data => console.log(data));
```

## 🔧 权限范围 (Scopes)

支持的权限范围：

- `read` - 读取权限
- `write` - 写入权限  
- `admin` - 管理权限
- `delete` - 删除权限

客户端只能访问其被授权的权限范围内的资源。

## 🛡️ 安全最佳实践

### 1. 客户端密钥安全

- 在客户端应用中安全存储 `client_secret`
- 使用环境变量或安全配置文件
- 定期轮换客户端凭据

### 2. API密钥管理

- 为不同环境使用不同的API密钥
- 设置适当的过期时间
- 监控API密钥使用情况
- 及时撤销泄露的密钥

### 3. 令牌管理

- 客户端令牌有限的生命周期（默认1小时）
- 实现自动令牌刷新
- 安全存储访问令牌

### 4. 网络安全

- 生产环境必须使用HTTPS
- 实现适当的重试和超时机制
- 记录和监控API访问

## 📊 客户端管理

### 查看客户端列表

```bash
curl -X GET "http://localhost:8000/api/v1/client/" \
  -H "Authorization: Bearer YOUR_USER_JWT_TOKEN"
```

### 更新客户端信息

```bash
curl -X PUT "http://localhost:8000/api/v1/client/client_abc123def456" \
  -H "Authorization: Bearer YOUR_USER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated App Name",
    "description": "Updated description",
    "is_active": true
  }'
```

### 撤销API密钥

```bash
curl -X DELETE "http://localhost:8000/api/v1/client/client_abc123def456/keys/ak_1_64" \
  -H "Authorization: Bearer YOUR_USER_JWT_TOKEN"
```

### 删除客户端

```bash
curl -X DELETE "http://localhost:8000/api/v1/client/client_abc123def456" \
  -H "Authorization: Bearer YOUR_USER_JWT_TOKEN"
```

## 🔍 认证验证

### 验证客户端令牌

```bash
curl -X GET "http://localhost:8000/api/v1/client/auth/verify" \
  -H "Authorization: Bearer YOUR_CLIENT_ACCESS_TOKEN"
```

**响应：**
```json
{
  "authenticated": true,
  "client_id": "client_abc123def456",
  "scopes": ["read", "write"],
  "token_type": "client_credentials",
  "expires_at": 1704102000
}
```

## 🚨 错误处理

### 常见错误码

- `400` - 请求参数错误
- `401` - 认证失败或令牌无效
- `403` - 权限不足
- `404` - 客户端或资源不存在
- `429` - 请求过于频繁（如果启用了速率限制）

### 错误响应格式

```json
{
  "error": "invalid_client",
  "message": "Invalid client credentials",
  "details": {
    "client_id": "client_abc123def456"
  }
}
```

## 🔧 配置选项

### 环境变量

```bash
# 客户端令牌设置
CLIENT_TOKEN_EXPIRE_MINUTES=60
API_KEY_EXPIRE_DAYS=365
MAX_CLIENTS_PER_USER=10

# 速率限制
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST=20
```

## 📚 API端点总览

### 客户端管理
- `POST /api/v1/client/register` - 注册客户端
- `GET /api/v1/client/` - 列出客户端
- `GET /api/v1/client/{client_id}` - 获取客户端详情
- `PUT /api/v1/client/{client_id}` - 更新客户端
- `DELETE /api/v1/client/{client_id}` - 删除客户端

### 令牌管理
- `POST /api/v1/client/token` - 获取客户端令牌
- `GET /api/v1/client/auth/verify` - 验证令牌

### API密钥管理
- `POST /api/v1/client/{client_id}/keys` - 创建API密钥
- `GET /api/v1/client/{client_id}/keys` - 列出API密钥
- `DELETE /api/v1/client/{client_id}/keys/{key_id}` - 撤销API密钥

这样您的API就完全支持外部客户端接入，无需任何Web重定向！