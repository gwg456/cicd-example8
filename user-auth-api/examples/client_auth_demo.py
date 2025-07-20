#!/usr/bin/env python3
"""
客户端认证演示脚本
演示如何使用客户端凭据流和API密钥认证
"""

import json
from datetime import datetime


def demonstrate_client_auth_concepts():
    """演示客户端认证概念"""
    print("🔐 客户端认证概念演示")
    print("=" * 60)
    
    concepts = {
        "客户端凭据流 (Client Credentials Flow)": {
            "description": "OAuth 2.0 标准的机器对机器认证流程",
            "use_cases": ["移动应用", "桌面应用", "后端服务", "API集成"],
            "advantages": ["无需用户交互", "自动化认证", "标准化流程"]
        },
        "API密钥认证": {
            "description": "基于密钥的简单认证方式",
            "use_cases": ["脚本自动化", "第三方集成", "简单API访问"],
            "advantages": ["简单易用", "无需复杂流程", "适合批量操作"]
        },
        "权限范围 (Scopes)": {
            "description": "细粒度的权限控制机制",
            "scopes": ["read", "write", "admin", "delete"],
            "benefits": ["最小权限原则", "安全控制", "灵活配置"]
        }
    }
    
    for concept, details in concepts.items():
        print(f"\n🔹 {concept}")
        print(f"   定义: {details['description']}")
        
        if 'use_cases' in details:
            print(f"   使用场景: {', '.join(details['use_cases'])}")
        if 'advantages' in details:
            print(f"   优势: {', '.join(details['advantages'])}")
        if 'scopes' in details:
            print(f"   权限范围: {', '.join(details['scopes'])}")
        if 'benefits' in details:
            print(f"   好处: {', '.join(details['benefits'])}")


def show_client_credentials_flow():
    """展示客户端凭据流程"""
    print("\n🚀 客户端凭据流程详解")
    print("=" * 60)
    
    steps = [
        {
            "step": "1. 用户注册客户端",
            "action": "通过用户账户在API中注册新的客户端应用",
            "endpoint": "POST /api/v1/client/register",
            "auth": "用户JWT令牌"
        },
        {
            "step": "2. 获取客户端凭据",
            "action": "系统返回client_id和client_secret",
            "note": "client_secret只显示一次，需要安全保存"
        },
        {
            "step": "3. 请求访问令牌",
            "action": "使用客户端凭据获取访问令牌",
            "endpoint": "POST /api/v1/client/token",
            "auth": "client_credentials grant"
        },
        {
            "step": "4. 使用访问令牌",
            "action": "在API请求中使用Bearer令牌",
            "format": "Authorization: Bearer <access_token>"
        },
        {
            "step": "5. 令牌过期处理",
            "action": "令牌过期后重新获取新令牌",
            "duration": "默认1小时有效期"
        }
    ]
    
    for step_info in steps:
        print(f"\n{step_info['step']}")
        print(f"   操作: {step_info['action']}")
        if 'endpoint' in step_info:
            print(f"   端点: {step_info['endpoint']}")
        if 'auth' in step_info:
            print(f"   认证: {step_info['auth']}")
        if 'note' in step_info:
            print(f"   注意: {step_info['note']}")
        if 'format' in step_info:
            print(f"   格式: {step_info['format']}")
        if 'duration' in step_info:
            print(f"   时长: {step_info['duration']}")


def show_api_examples():
    """展示API使用示例"""
    print("\n💻 API使用示例")
    print("=" * 60)
    
    print("\n📋 1. 注册客户端")
    register_example = {
        "method": "POST",
        "url": "/api/v1/client/register",
        "headers": {
            "Authorization": "Bearer <USER_JWT_TOKEN>",
            "Content-Type": "application/json"
        },
        "body": {
            "name": "My Mobile App",
            "description": "iOS/Android应用",
            "scopes": ["read", "write"],
            "is_trusted": False,
            "expires_days": 365
        }
    }
    
    print(f"   请求: {register_example['method']} {register_example['url']}")
    print(f"   Headers: {json.dumps(register_example['headers'], indent=8)}")
    print(f"   Body: {json.dumps(register_example['body'], indent=8, ensure_ascii=False)}")
    
    register_response = {
        "id": 1,
        "client_id": "client_abc123def456",
        "client_secret": "secret_xyz789uvw012",
        "name": "My Mobile App",
        "scopes": ["read", "write"],
        "is_active": True,
        "created_at": "2024-01-01T10:00:00Z"
    }
    print(f"   响应: {json.dumps(register_response, indent=8, ensure_ascii=False)}")
    
    print("\n📋 2. 获取访问令牌")
    token_example = {
        "method": "POST",
        "url": "/api/v1/client/token",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": {
            "grant_type": "client_credentials",
            "client_id": "client_abc123def456",
            "client_secret": "secret_xyz789uvw012",
            "scope": "read write"
        }
    }
    
    print(f"   请求: {token_example['method']} {token_example['url']}")
    print(f"   Headers: {json.dumps(token_example['headers'], indent=8)}")
    print(f"   Body: {json.dumps(token_example['body'], indent=8)}")
    
    token_response = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": "read write"
    }
    print(f"   响应: {json.dumps(token_response, indent=8)}")
    
    print("\n📋 3. 使用令牌访问API")
    api_example = {
        "method": "GET",
        "url": "/api/v1/users/me",
        "headers": {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    }
    
    print(f"   请求: {api_example['method']} {api_example['url']}")
    print(f"   Headers: {json.dumps(api_example['headers'], indent=8)}")


def show_api_key_examples():
    """展示API密钥示例"""
    print("\n🗝️ API密钥认证示例")
    print("=" * 60)
    
    print("\n📋 1. 创建API密钥")
    key_create = {
        "method": "POST",
        "url": "/api/v1/client/client_abc123def456/keys",
        "headers": {
            "Authorization": "Bearer <USER_JWT_TOKEN>",
            "Content-Type": "application/json"
        },
        "body": {
            "name": "Production API Key",
            "scopes": ["read"],
            "expires_days": 30
        }
    }
    
    print(f"   请求: {key_create['method']} {key_create['url']}")
    print(f"   Headers: {json.dumps(key_create['headers'], indent=8)}")
    print(f"   Body: {json.dumps(key_create['body'], indent=8, ensure_ascii=False)}")
    
    key_response = {
        "id": 1,
        "key_id": "ak_1_64",
        "key_value": "ak_1234567890abcdef1234567890abcdef",
        "name": "Production API Key",
        "scopes": ["read"],
        "expires_at": "2024-02-01T10:00:00Z"
    }
    print(f"   响应: {json.dumps(key_response, indent=8, ensure_ascii=False)}")
    
    print("\n📋 2. 使用API密钥（简单方式）")
    simple_api = {
        "method": "GET",
        "url": "/api/v1/users/me",
        "headers": {
            "X-API-Key": "ak_1234567890abcdef1234567890abcdef"
        }
    }
    
    print(f"   请求: {simple_api['method']} {simple_api['url']}")
    print(f"   Headers: {json.dumps(simple_api['headers'], indent=8)}")
    
    print("\n📋 3. 使用API密钥（签名方式）")
    print("   更安全的签名认证方式:")
    signature_steps = [
        "1. 生成时间戳: timestamp = current_unix_timestamp",
        "2. 构建签名字符串: string_to_sign = api_key + ':' + timestamp",
        "3. 计算HMAC-SHA256签名: signature = HMAC-SHA256(client_secret, string_to_sign)",
        "4. Base64编码签名: signature_b64 = base64.encode(signature)"
    ]
    
    for step in signature_steps:
        print(f"      {step}")
    
    signature_api = {
        "method": "GET",
        "url": "/api/v1/users/me",
        "headers": {
            "X-API-Key": "ak_1234567890abcdef1234567890abcdef",
            "X-API-Timestamp": "1704067200",
            "X-API-Signature": "abcd1234efgh5678..."
        }
    }
    
    print(f"   请求: {signature_api['method']} {signature_api['url']}")
    print(f"   Headers: {json.dumps(signature_api['headers'], indent=8)}")


def show_python_client_example():
    """展示Python客户端示例"""
    print("\n🐍 Python客户端实现示例")
    print("=" * 60)
    
    python_code = '''
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
        self.token_expires_at = 0
    
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
            # 设置过期时间（提前5分钟刷新）
            self.token_expires_at = time.time() + data["expires_in"] - 300
            return self.access_token
        else:
            raise Exception(f"Failed to get token: {response.text}")
    
    def ensure_valid_token(self):
        """确保令牌有效"""
        if not self.access_token or time.time() >= self.token_expires_at:
            self.get_client_token()
    
    def api_request(self, method, endpoint, **kwargs):
        """发送API请求"""
        self.ensure_valid_token()
        
        headers = kwargs.pop('headers', {})
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

# 自动获取令牌并调用API
response = client.api_request('GET', '/api/v1/users/me')
if response.status_code == 200:
    user_data = response.json()
    print("用户信息:", user_data)
else:
    print("请求失败:", response.text)
'''
    
    print(python_code)


def show_security_considerations():
    """展示安全考虑"""
    print("\n🛡️ 安全考虑事项")
    print("=" * 60)
    
    security_items = {
        "客户端密钥保护": [
            "永远不要在客户端代码中硬编码client_secret",
            "使用环境变量或安全配置文件存储凭据",
            "在移动应用中使用安全存储机制",
            "定期轮换客户端凭据"
        ],
        "令牌管理": [
            "令牌有限的生命周期（默认1小时）",
            "实现自动令牌刷新机制",
            "安全存储访问令牌",
            "不要在URL中传递令牌"
        ],
        "API密钥安全": [
            "为不同环境使用不同的API密钥",
            "设置适当的过期时间",
            "监控API密钥使用情况",
            "生产环境使用签名认证"
        ],
        "网络安全": [
            "生产环境必须使用HTTPS",
            "实现速率限制和防DDoS",
            "记录和监控API访问",
            "实现适当的错误处理"
        ]
    }
    
    for category, items in security_items.items():
        print(f"\n📌 {category}")
        for item in items:
            print(f"   • {item}")


def show_vs_comparison():
    """对比不同认证方式"""
    print("\n⚖️ 认证方式对比")
    print("=" * 60)
    
    comparison = {
        "用户JWT认证": {
            "适用场景": "用户相关操作，需要用户上下文",
            "获取方式": "用户名密码登录",
            "生命周期": "短期（30分钟）",
            "使用复杂度": "中等"
        },
        "客户端凭据流": {
            "适用场景": "机器对机器通信，后台服务",
            "获取方式": "client_id + client_secret",
            "生命周期": "中期（1小时）",
            "使用复杂度": "简单"
        },
        "API密钥认证": {
            "适用场景": "脚本自动化，简单集成",
            "获取方式": "直接使用密钥",
            "生命周期": "长期（可配置）",
            "使用复杂度": "最简单"
        },
        "OIDC认证": {
            "适用场景": "第三方身份验证，SSO",
            "获取方式": "第三方提供商",
            "生命周期": "变化（依赖提供商）",
            "使用复杂度": "复杂"
        }
    }
    
    for method, details in comparison.items():
        print(f"\n🔹 {method}")
        for key, value in details.items():
            print(f"   {key}: {value}")


def show_api_endpoints():
    """展示所有API端点"""
    print("\n📚 API端点总览")
    print("=" * 60)
    
    endpoints = {
        "客户端管理": [
            ("POST", "/api/v1/client/register", "注册新客户端"),
            ("GET", "/api/v1/client/", "列出所有客户端"),
            ("GET", "/api/v1/client/{client_id}", "获取客户端详情"),
            ("PUT", "/api/v1/client/{client_id}", "更新客户端"),
            ("DELETE", "/api/v1/client/{client_id}", "删除客户端")
        ],
        "令牌管理": [
            ("POST", "/api/v1/client/token", "获取客户端令牌"),
            ("GET", "/api/v1/client/auth/verify", "验证令牌")
        ],
        "API密钥管理": [
            ("POST", "/api/v1/client/{client_id}/keys", "创建API密钥"),
            ("GET", "/api/v1/client/{client_id}/keys", "列出API密钥"),
            ("DELETE", "/api/v1/client/{client_id}/keys/{key_id}", "撤销API密钥")
        ],
        "用户认证": [
            ("POST", "/api/v1/auth/login/json", "用户登录"),
            ("POST", "/api/v1/auth/register", "用户注册"),
            ("GET", "/api/v1/users/me", "获取当前用户信息")
        ]
    }
    
    for category, endpoint_list in endpoints.items():
        print(f"\n📂 {category}")
        for method, path, description in endpoint_list:
            print(f"   {method:<6} {path:<40} {description}")


def main():
    """主演示函数"""
    print("🎭 客户端认证完整演示")
    print("🔄 从OIDC重定向到客户端凭据流的转换")
    print("=" * 60)
    
    # 概念演示
    demonstrate_client_auth_concepts()
    
    # 流程演示
    show_client_credentials_flow()
    
    # API示例
    show_api_examples()
    
    # API密钥示例
    show_api_key_examples()
    
    # Python客户端示例
    show_python_client_example()
    
    # 安全考虑
    show_security_considerations()
    
    # 对比分析
    show_vs_comparison()
    
    # API端点
    show_api_endpoints()
    
    print("\n🎯 总结：从OIDC到客户端认证的转换")
    print("=" * 60)
    
    summary = {
        "之前 (OIDC重定向模式)": [
            "需要Web浏览器交互",
            "重定向到第三方提供商",
            "适合Web应用",
            "用户手动授权"
        ],
        "现在 (客户端凭据模式)": [
            "纯API交互，无需浏览器",
            "机器对机器认证",
            "适合移动/桌面应用",
            "自动化认证流程",
            "支持多种认证方式"
        ]
    }
    
    for approach, features in summary.items():
        print(f"\n{approach}")
        for feature in features:
            print(f"   • {feature}")
    
    print("\n🎉 恭喜！您的API现在完全支持外部客户端接入")
    print("\n📖 下一步:")
    print("• 创建客户端应用并注册")
    print("• 实现客户端凭据流")
    print("• 配置API密钥认证")
    print("• 部署和监控客户端访问")
    
    print("\n📚 参考文档:")
    print("• 客户端认证指南: docs/CLIENT_AUTH_GUIDE.md")
    print("• API文档: http://localhost:8000/docs")
    print("• OAuth 2.0规范: https://tools.ietf.org/html/rfc6749")


if __name__ == "__main__":
    main()