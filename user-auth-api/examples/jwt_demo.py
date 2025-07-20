#!/usr/bin/env python3
"""
JWT Token 获取和使用演示脚本
演示如何获取JWT token并使用它访问受保护的API端点
"""

import json
import time
from datetime import datetime, timedelta
from jose import jwt

# 模拟配置 (实际使用时从环境变量获取)
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token_demo(data: dict, expires_delta: timedelta = None):
    """演示JWT Token创建过程"""
    print("🔧 创建JWT Token...")
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 添加过期时间到payload
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()  # 签发时间
    })
    
    print(f"📋 Token Payload: {json.dumps(to_encode, default=str, indent=2)}")
    
    # 生成JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    print(f"🎫 生成的JWT Token: {encoded_jwt}")
    print(f"⏰ Token过期时间: {expire}")
    
    return encoded_jwt

def verify_token_demo(token: str):
    """演示JWT Token验证过程"""
    print("\n🔍 验证JWT Token...")
    
    try:
        # 解码token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ Token验证成功!")
        print(f"📋 Token内容: {json.dumps(payload, default=str, indent=2)}")
        
        username = payload.get("sub")
        exp = payload.get("exp")
        
        if exp:
            exp_datetime = datetime.fromtimestamp(exp)
            print(f"👤 用户名: {username}")
            print(f"⏰ 过期时间: {exp_datetime}")
            
            if datetime.utcnow().timestamp() > exp:
                print("⚠️  Token已过期!")
                return None
            else:
                remaining = exp_datetime - datetime.utcnow()
                print(f"⏳ 剩余时间: {remaining}")
        
        return username
        
    except jwt.ExpiredSignatureError:
        print("❌ Token已过期!")
        return None
    except jwt.JWTError as e:
        print(f"❌ Token验证失败: {e}")
        return None

def login_flow_demo():
    """演示完整的登录流程"""
    print("🚀 JWT Token 获取流程演示")
    print("=" * 50)
    
    # 1. 模拟用户登录
    print("\n📝 步骤1: 用户登录")
    username = "testuser"
    password = "password123"
    print(f"用户名: {username}")
    print(f"密码: {password}")
    
    # 2. 验证用户凭据 (这里跳过密码验证演示)
    print("\n🔐 步骤2: 验证用户凭据")
    print("✅ 用户名和密码验证通过")
    
    # 3. 创建JWT Token
    print("\n🎫 步骤3: 创建JWT Token")
    token_data = {"sub": username}
    access_token = create_access_token_demo(token_data)
    
    # 4. 返回token给客户端
    print("\n📤 步骤4: 返回Token给客户端")
    response = {
        "access_token": access_token,
        "token_type": "bearer"
    }
    print(f"API响应: {json.dumps(response, indent=2)}")
    
    # 5. 客户端使用token访问受保护资源
    print("\n🔒 步骤5: 使用Token访问受保护资源")
    print(f"Authorization Header: Bearer {access_token}")
    
    # 6. 服务器验证token
    print("\n🛡️  步骤6: 服务器验证Token")
    verified_username = verify_token_demo(access_token)
    
    if verified_username:
        print(f"\n✅ 访问成功! 当前用户: {verified_username}")
        print("🎯 可以访问受保护的资源")
    else:
        print("\n❌ 访问失败! Token无效")

def practical_examples():
    """实际使用示例"""
    print("\n" + "=" * 50)
    print("📚 实际使用示例")
    print("=" * 50)
    
    print("\n🐍 Python requests示例:")
    print("""
import requests

# 1. 登录获取token
login_url = "http://localhost:8000/api/v1/auth/login/json"
login_data = {
    "username": "testuser",
    "password": "password123"
}

response = requests.post(login_url, json=login_data)
if response.status_code == 200:
    token_info = response.json()
    access_token = token_info["access_token"]
    
    # 2. 使用token访问受保护资源
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 获取用户信息
    user_response = requests.get(
        "http://localhost:8000/api/v1/users/me", 
        headers=headers
    )
    
    if user_response.status_code == 200:
        user_info = user_response.json()
        print("用户信息:", user_info)
    else:
        print("获取用户信息失败:", user_response.text)
else:
    print("登录失败:", response.text)
""")
    
    print("\n🌐 cURL示例:")
    print("""
# 1. 登录获取token
curl -X POST "http://localhost:8000/api/v1/auth/login/json" \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# 响应示例:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }

# 2. 使用token访问受保护资源
curl -X GET "http://localhost:8000/api/v1/users/me" \\
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
""")

def api_endpoints_overview():
    """API端点概览"""
    print("\n" + "=" * 50)
    print("🎯 API端点概览")
    print("=" * 50)
    
    endpoints = [
        {
            "method": "POST",
            "path": "/api/v1/auth/register",
            "description": "用户注册",
            "auth": "无需认证"
        },
        {
            "method": "POST", 
            "path": "/api/v1/auth/login",
            "description": "登录 (表单格式)",
            "auth": "无需认证"
        },
        {
            "method": "POST",
            "path": "/api/v1/auth/login/json", 
            "description": "登录 (JSON格式)",
            "auth": "无需认证"
        },
        {
            "method": "GET",
            "path": "/api/v1/users/me",
            "description": "获取当前用户信息",
            "auth": "需要JWT Token"
        },
        {
            "method": "PUT",
            "path": "/api/v1/users/me",
            "description": "更新当前用户信息", 
            "auth": "需要JWT Token"
        },
        {
            "method": "GET",
            "path": "/api/v1/users",
            "description": "获取用户列表",
            "auth": "需要JWT Token (管理员)"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n📍 {endpoint['method']} {endpoint['path']}")
        print(f"   描述: {endpoint['description']}")
        print(f"   认证: {endpoint['auth']}")

if __name__ == "__main__":
    # 运行演示
    login_flow_demo()
    practical_examples()
    api_endpoints_overview()
    
    print("\n🎉 演示完成!")
    print("\n💡 提示:")
    print("- 在生产环境中，请使用强密钥并通过环境变量配置")
    print("- 建议设置合适的token过期时间")
    print("- 实现token刷新机制以提升用户体验")
    print("- 考虑使用HTTPS确保token传输安全")