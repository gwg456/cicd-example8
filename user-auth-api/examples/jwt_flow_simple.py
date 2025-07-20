#!/usr/bin/env python3
"""
JWT Token 获取流程简化演示
不依赖外部库，纯Python演示JWT Token的获取和使用流程
"""

import json
import base64
from datetime import datetime, timedelta

def jwt_flow_explanation():
    """详细解释JWT Token获取流程"""
    print("🔑 JWT Token 获取流程详解")
    print("=" * 60)
    
    print("\n📋 流程概述:")
    print("1️⃣  用户注册 (如果还没有账户)")
    print("2️⃣  用户登录 (提供用户名和密码)")
    print("3️⃣  服务器验证凭据")
    print("4️⃣  服务器生成JWT Token")
    print("5️⃣  返回Token给客户端")
    print("6️⃣  客户端在后续请求中携带Token")
    print("7️⃣  服务器验证Token并提供服务")
    
    print("\n" + "=" * 60)
    print("详细步骤演示:")
    
    # 步骤1: 用户注册
    print("\n1️⃣  【用户注册】")
    print("📍 端点: POST /api/v1/auth/register")
    print("📤 请求数据:")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }
    print(json.dumps(register_data, indent=2, ensure_ascii=False))
    
    print("\n📥 响应数据:")
    register_response = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": "2024-01-01T10:00:00Z"
    }
    print(json.dumps(register_response, indent=2, ensure_ascii=False))
    
    # 步骤2: 用户登录
    print("\n\n2️⃣  【用户登录】")
    print("📍 端点: POST /api/v1/auth/login/json")
    print("📤 请求数据:")
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    print(json.dumps(login_data, indent=2, ensure_ascii=False))
    
    # 步骤3: 服务器验证
    print("\n\n3️⃣  【服务器验证凭据】")
    print("🔍 服务器执行的操作:")
    print("   a) 根据用户名查询数据库")
    print("   b) 比较提交的密码与存储的密码哈希")
    print("   c) 检查用户状态 (是否激活)")
    print("   ✅ 验证通过")
    
    # 步骤4: 生成JWT Token
    print("\n\n4️⃣  【生成JWT Token】")
    print("🔧 Token生成过程:")
    
    # JWT Header
    header = {"alg": "HS256", "typ": "JWT"}
    print(f"📋 Header: {json.dumps(header, indent=2)}")
    
    # JWT Payload
    now = datetime.utcnow()
    expire_time = now + timedelta(minutes=60)
    payload = {
        "sub": "testuser",  # 用户名
        "exp": int(expire_time.timestamp()),  # 过期时间戳
        "iat": int(now.timestamp())  # 签发时间戳
    }
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    # Base64编码演示 (实际JWT会用更复杂的编码)
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    print(f"🔤 Header (Base64): {header_b64}")
    print(f"🔤 Payload (Base64): {payload_b64}")
    print(f"🔐 Signature: [使用SECRET_KEY和HS256算法生成]")
    
    # 模拟完整的JWT
    fake_signature = "xyz123abc456def789"
    jwt_token = f"{header_b64}.{payload_b64}.{fake_signature}"
    print(f"🎫 完整JWT Token: {jwt_token}")
    
    # 步骤5: 返回Token
    print("\n\n5️⃣  【返回Token给客户端】")
    print("📥 API响应:")
    token_response = {
        "access_token": jwt_token,
        "token_type": "bearer"
    }
    print(json.dumps(token_response, indent=2, ensure_ascii=False))
    
    # 步骤6: 使用Token
    print("\n\n6️⃣  【客户端使用Token】")
    print("📤 后续请求格式:")
    print("GET /api/v1/users/me HTTP/1.1")
    print("Host: localhost:8000")
    print(f"Authorization: Bearer {jwt_token}")
    print("Content-Type: application/json")
    
    # 步骤7: 服务器验证Token
    print("\n\n7️⃣  【服务器验证Token】")
    print("🔍 Token验证过程:")
    print("   a) 从Authorization header提取Token")
    print("   b) 验证Token签名")
    print("   c) 检查Token是否过期")
    print("   d) 提取用户信息 (sub字段)")
    print("   e) 查询用户是否仍然有效")
    print("   ✅ 验证通过，返回受保护的数据")

def api_usage_examples():
    """API使用示例"""
    print("\n\n" + "=" * 60)
    print("🛠️  实际API使用示例")
    print("=" * 60)
    
    print("\n🐍 Python + requests 示例:")
    python_example = '''
import requests

# 1. 登录获取Token
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login/json",
    json={
        "username": "testuser",
        "password": "password123"
    }
)

if login_response.status_code == 200:
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # 2. 使用Token访问受保护资源
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 获取当前用户信息
    user_response = requests.get(
        "http://localhost:8000/api/v1/users/me",
        headers=headers
    )
    
    if user_response.status_code == 200:
        user_info = user_response.json()
        print("用户信息:", user_info)
    else:
        print("请求失败:", user_response.text)
else:
    print("登录失败:", login_response.text)
'''
    print(python_example)
    
    print("\n🌐 cURL 示例:")
    curl_example = '''
# 1. 登录获取Token
curl -X POST "http://localhost:8000/api/v1/auth/login/json" \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# 响应: {"access_token": "eyJ...", "token_type": "bearer"}

# 2. 使用Token访问受保护资源
curl -X GET "http://localhost:8000/api/v1/users/me" \\
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
'''
    print(curl_example)
    
    print("\n🟨 JavaScript (fetch) 示例:")
    js_example = '''
// 1. 登录获取Token
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login/json', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'testuser',
    password: 'password123'
  })
});

if (loginResponse.ok) {
  const tokenData = await loginResponse.json();
  const accessToken = tokenData.access_token;
  
  // 2. 使用Token访问受保护资源
  const userResponse = await fetch('http://localhost:8000/api/v1/users/me', {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  
  if (userResponse.ok) {
    const userInfo = await userResponse.json();
    console.log('用户信息:', userInfo);
  } else {
    console.error('请求失败:', await userResponse.text());
  }
} else {
  console.error('登录失败:', await loginResponse.text());
}
'''
    print(js_example)

def security_considerations():
    """安全注意事项"""
    print("\n\n" + "=" * 60)
    print("🛡️  安全注意事项")
    print("=" * 60)
    
    considerations = [
        {
            "title": "密钥安全",
            "description": "SECRET_KEY必须保密，使用环境变量存储",
            "example": "export SECRET_KEY='your-very-secret-key-here'"
        },
        {
            "title": "Token过期时间",
            "description": "设置合理的过期时间，平衡安全性和用户体验",
            "example": "ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1小时"
        },
        {
            "title": "HTTPS传输",
            "description": "在生产环境中必须使用HTTPS传输Token",
            "example": "https://api.example.com/api/v1/auth/login"
        },
        {
            "title": "Token存储",
            "description": "客户端应安全存储Token，避免XSS攻击",
            "example": "使用HttpOnly Cookie或安全的本地存储"
        },
        {
            "title": "密码强度",
            "description": "强制要求强密码，使用bcrypt哈希",
            "example": "最少8位，包含大小写字母、数字和特殊字符"
        }
    ]
    
    for i, item in enumerate(considerations, 1):
        print(f"\n{i}. {item['title']}")
        print(f"   说明: {item['description']}")
        print(f"   示例: {item['example']}")

def available_endpoints():
    """可用的API端点"""
    print("\n\n" + "=" * 60)
    print("🎯 可用的API端点")
    print("=" * 60)
    
    endpoints = [
        ("POST", "/api/v1/auth/register", "用户注册", "无需认证"),
        ("POST", "/api/v1/auth/login", "用户登录 (表单)", "无需认证"),
        ("POST", "/api/v1/auth/login/json", "用户登录 (JSON)", "无需认证"),
        ("GET", "/api/v1/users/me", "获取当前用户信息", "需要Token"),
        ("PUT", "/api/v1/users/me", "更新当前用户信息", "需要Token"),
        ("POST", "/api/v1/users/me/change-password", "修改密码", "需要Token"),
        ("GET", "/api/v1/users", "获取用户列表", "需要Token (管理员)"),
        ("GET", "/api/v1/users/{user_id}", "获取指定用户信息", "需要Token (管理员)"),
        ("PUT", "/api/v1/users/{user_id}/activate", "激活用户", "需要Token (管理员)"),
        ("DELETE", "/api/v1/users/{user_id}", "删除用户", "需要Token (管理员)"),
    ]
    
    for method, path, description, auth in endpoints:
        print(f"\n📍 {method:<6} {path}")
        print(f"   描述: {description}")
        print(f"   认证: {auth}")

if __name__ == "__main__":
    jwt_flow_explanation()
    api_usage_examples()
    security_considerations()
    available_endpoints()
    
    print("\n\n🎉 JWT Token流程演示完成!")
    print("\n💡 快速开始:")
    print("1. 启动FastAPI服务: uvicorn app.main:app --reload")
    print("2. 访问API文档: http://localhost:8000/docs")
    print("3. 注册用户并获取Token")
    print("4. 使用Token访问受保护的API")