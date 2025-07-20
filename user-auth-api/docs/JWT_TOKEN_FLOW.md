# JWT Token 获取流程详解

## 🔑 JWT Token 获取的完整流程

### 1. 用户注册 (可选，如果还没有账户)

**端点**: `POST /api/v1/auth/register`

```json
{
  "username": "testuser",
  "email": "test@example.com", 
  "password": "password123",
  "full_name": "Test User"
}
```

**响应**:
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "Test User",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T10:00:00Z"
}
```

### 2. 获取 JWT Token (登录)

有两种方式获取JWT Token：

#### 方式一：表单登录 (OAuth2 标准)
**端点**: `POST /api/v1/auth/login`
**Content-Type**: `application/x-www-form-urlencoded`

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

#### 方式二：JSON 登录
**端点**: `POST /api/v1/auth/login/json`
**Content-Type**: `application/json`

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

**成功响应** (两种方式相同):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcwNDEwMjAwMH0.xyz123...",
  "token_type": "bearer"
}
```

### 3. 使用 JWT Token 访问受保护的端点

获取到token后，在请求头中添加Authorization：

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcwNDEwMjAwMH0.xyz123..."
```

## 🔧 技术实现流程

### 1. 登录验证流程
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Database
    participant JWT
    
    Client->>API: POST /auth/login (username, password)
    API->>Database: 查询用户信息
    Database-->>API: 返回用户数据
    API->>API: 验证密码 (bcrypt)
    API->>JWT: 创建JWT Token
    JWT-->>API: 返回 token
    API-->>Client: 返回 {access_token, token_type}
```

### 2. Token 验证流程
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant JWT
    participant Database
    
    Client->>API: 请求受保护资源 (Bearer token)
    API->>JWT: 验证 token 签名
    JWT-->>API: 返回用户名 (sub)
    API->>Database: 查询用户信息
    Database-->>API: 返回用户数据
    API-->>Client: 返回受保护的数据
```

## 📋 JWT Token 详细信息

### Token 结构
JWT Token 包含三部分，用点号分隔：
```
Header.Payload.Signature
```

#### Header (头部)
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

#### Payload (载荷)
```json
{
  "sub": "testuser",     // 用户名
  "exp": 1704102000,     // 过期时间戳
  "iat": 1704098400      // 签发时间戳
}
```

#### Signature (签名)
使用HS256算法和SECRET_KEY生成

### Token 配置
- **算法**: HS256
- **默认过期时间**: 60分钟 (可在config.py中配置)
- **密钥**: 通过环境变量 `SECRET_KEY` 设置

## 🛡️ 安全特性

1. **密码哈希**: 使用bcrypt算法加盐哈希存储密码
2. **Token过期**: JWT包含过期时间，自动失效
3. **密钥保护**: 使用环境变量存储签名密钥
4. **用户状态检查**: 验证用户是否处于活跃状态

## 🔍 错误处理

### 登录失败
```json
{
  "detail": "Incorrect username or password"
}
```
**HTTP状态码**: 401 Unauthorized

### Token无效
```json
{
  "detail": "Could not validate credentials"
}
```
**HTTP状态码**: 401 Unauthorized

### 用户未激活
```json
{
  "detail": "Inactive user"
}
```
**HTTP状态码**: 400 Bad Request

## 📝 实际使用示例

### Python 示例
```python
import requests

# 1. 登录获取token
login_data = {
    "username": "testuser",
    "password": "password123"
}
response = requests.post("http://localhost:8000/api/v1/auth/login/json", json=login_data)
token_data = response.json()
access_token = token_data["access_token"]

# 2. 使用token访问受保护资源
headers = {"Authorization": f"Bearer {access_token}"}
user_response = requests.get("http://localhost:8000/api/v1/users/me", headers=headers)
user_info = user_response.json()
print(user_info)
```

### JavaScript 示例
```javascript
// 1. 登录获取token
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login/json', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'testuser',
    password: 'password123'
  })
});
const tokenData = await loginResponse.json();
const accessToken = tokenData.access_token;

// 2. 使用token访问受保护资源
const userResponse = await fetch('http://localhost:8000/api/v1/users/me', {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
const userInfo = await userResponse.json();
console.log(userInfo);
```

## ⚙️ 配置选项

在 `app/config.py` 中可以配置：

```python
# JWT配置
SECRET_KEY: str = "your-secret-key"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
```

通过环境变量设置：
```bash
export SECRET_KEY="your-super-secret-key"
export ACCESS_TOKEN_EXPIRE_MINUTES=120
```