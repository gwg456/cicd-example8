#!/usr/bin/env python3
"""
OIDC Authentication Demo
演示 OIDC 认证流程的完整示例
"""

import json
import requests
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional


class OIDCDemo:
    """OIDC认证演示类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_available_providers(self) -> Dict[str, Any]:
        """获取可用的OIDC提供商"""
        print("🔍 获取可用的OIDC提供商...")
        
        response = self.session.get(f"{self.base_url}/api/v1/auth/oidc/providers")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 找到 {data['count']} 个可用提供商")
            
            for provider in data['providers']:
                print(f"   📍 {provider['display_name']} ({provider['name']})")
                print(f"      登录URL: {provider['login_url']}")
            
            return data
        else:
            print(f"❌ 获取提供商失败: {response.status_code}")
            return {}
    
    def simulate_oidc_flow(self, provider_name: str):
        """模拟OIDC认证流程"""
        print(f"\n🚀 开始 {provider_name} OIDC 认证流程模拟...")
        
        # 步骤1: 启动OIDC登录
        print("\n1️⃣ 启动OIDC登录...")
        login_url = f"{self.base_url}/api/v1/auth/oidc/login/{provider_name}"
        print(f"访问: {login_url}")
        
        # 实际使用中，这会重定向到OIDC提供商
        response = self.session.get(login_url, allow_redirects=False)
        
        if response.status_code == 302:
            redirect_url = response.headers.get('Location')
            print(f"✅ 重定向到OIDC提供商: {redirect_url[:100]}...")
            
            # 解析重定向URL
            parsed_url = urlparse(redirect_url)
            params = parse_qs(parsed_url.query)
            
            print(f"   📋 认证参数:")
            print(f"      Client ID: {params.get('client_id', ['N/A'])[0]}")
            print(f"      Response Type: {params.get('response_type', ['N/A'])[0]}")
            print(f"      Scope: {params.get('scope', ['N/A'])[0]}")
            print(f"      State: {params.get('state', ['N/A'])[0][:20]}...")
            
            if 'nonce' in params:
                print(f"      Nonce: {params['nonce'][0][:20]}...")
            if 'code_challenge' in params:
                print(f"      PKCE Challenge: {params['code_challenge'][0][:20]}...")
            
            return {
                "redirect_url": redirect_url,
                "state": params.get('state', [None])[0],
                "provider": provider_name
            }
        else:
            print(f"❌ 登录失败: {response.status_code}")
            return None
    
    def simulate_callback(self, provider_name: str, auth_code: str, state: str):
        """模拟OIDC回调处理"""
        print(f"\n2️⃣ 模拟OIDC回调处理...")
        
        callback_url = f"{self.base_url}/api/v1/auth/oidc/callback/{provider_name}"
        params = {
            "code": auth_code,
            "state": state
        }
        
        print(f"回调URL: {callback_url}")
        print(f"授权码: {auth_code[:20]}...")
        print(f"State: {state[:20]}...")
        
        # 注意：实际环境中需要正确的session cookie
        response = self.session.get(callback_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ OIDC认证成功!")
            print(f"   🎫 Access Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"   👤 用户信息:")
            user = data.get('user', {})
            print(f"      ID: {user.get('id')}")
            print(f"      用户名: {user.get('username')}")
            print(f"      邮箱: {user.get('email')}")
            print(f"      全名: {user.get('full_name')}")
            print(f"      提供商: {user.get('provider')}")
            
            return data
        else:
            print(f"❌ 回调处理失败: {response.status_code}")
            if response.content:
                print(f"错误详情: {response.text}")
            return None
    
    def test_protected_endpoint(self, access_token: str):
        """测试使用access token访问受保护端点"""
        print(f"\n3️⃣ 测试受保护端点访问...")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self.session.get(
            f"{self.base_url}/api/v1/users/me",
            headers=headers
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print("✅ 成功访问受保护端点!")
            print(f"   用户详细信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
            return user_info
        else:
            print(f"❌ 访问受保护端点失败: {response.status_code}")
            return None
    
    def demonstrate_logout(self, provider_name: str, id_token: Optional[str] = None):
        """演示OIDC注销流程"""
        print(f"\n4️⃣ 演示OIDC注销流程...")
        
        logout_url = f"{self.base_url}/api/v1/auth/oidc/logout/{provider_name}"
        payload = {}
        
        if id_token:
            payload["id_token_hint"] = id_token
        
        response = self.session.post(logout_url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 注销请求成功!")
            
            if data.get('logout_url'):
                print(f"   🔗 提供商注销URL: {data['logout_url']}")
                print("   用户需要访问此URL完成提供商注销")
            else:
                print(f"   📝 消息: {data.get('message', '注销完成')}")
            
            return data
        else:
            print(f"❌ 注销失败: {response.status_code}")
            return None


def demonstrate_oidc_concepts():
    """演示OIDC概念和术语"""
    print("📚 OIDC (OpenID Connect) 概念演示")
    print("=" * 60)
    
    concepts = {
        "OIDC": {
            "description": "基于OAuth 2.0的身份认证层",
            "benefits": ["标准化", "安全", "互操作性", "广泛支持"]
        },
        "ID Token": {
            "description": "包含用户身份信息的JWT",
            "contents": ["用户ID (sub)", "签发者 (iss)", "受众 (aud)", "过期时间 (exp)"]
        },
        "Access Token": {
            "description": "用于访问受保护资源的令牌",
            "usage": "API调用的Authorization header"
        },
        "Authorization Code Flow": {
            "description": "最安全的OIDC认证流程",
            "steps": ["重定向到提供商", "用户认证", "返回授权码", "交换令牌"]
        },
        "PKCE": {
            "description": "增强OAuth安全性的机制",
            "protection": "防止授权码拦截攻击"
        },
        "State参数": {
            "description": "防止CSRF攻击的随机值",
            "verification": "回调时必须验证state值"
        },
        "Nonce": {
            "description": "防止ID Token重放攻击",
            "binding": "绑定认证请求和ID Token"
        }
    }
    
    for concept, details in concepts.items():
        print(f"\n🔹 {concept}")
        print(f"   定义: {details['description']}")
        
        if 'benefits' in details:
            print(f"   优势: {', '.join(details['benefits'])}")
        if 'contents' in details:
            print(f"   内容: {', '.join(details['contents'])}")
        if 'usage' in details:
            print(f"   用途: {details['usage']}")
        if 'steps' in details:
            print(f"   步骤: {' → '.join(details['steps'])}")
        if 'protection' in details:
            print(f"   保护: {details['protection']}")
        if 'verification' in details:
            print(f"   验证: {details['verification']}")
        if 'binding' in details:
            print(f"   绑定: {details['binding']}")


def show_oidc_vs_traditional():
    """对比OIDC与传统认证"""
    print("\n⚖️  OIDC vs 传统用户名密码认证")
    print("=" * 60)
    
    comparison = {
        "安全性": {
            "OIDC": "委托给专业提供商，多因素认证，定期安全更新",
            "传统": "需要自行实现密码策略，安全风险自担"
        },
        "用户体验": {
            "OIDC": "一键登录，无需记住密码，单点登录",
            "传统": "需要为每个应用注册账户和密码"
        },
        "开发复杂度": {
            "OIDC": "集成相对简单，标准化流程",
            "传统": "需要实现完整的认证系统"
        },
        "维护成本": {
            "OIDC": "提供商负责安全维护",
            "传统": "需要持续维护和更新安全措施"
        },
        "依赖性": {
            "OIDC": "依赖外部提供商的可用性",
            "传统": "完全自主控制"
        },
        "数据控制": {
            "OIDC": "用户数据部分存储在提供商",
            "传统": "完全控制用户数据"
        }
    }
    
    for aspect, details in comparison.items():
        print(f"\n📊 {aspect}")
        print(f"   OIDC:  {details['OIDC']}")
        print(f"   传统:  {details['传统']}")


def main():
    """主演示函数"""
    print("🎭 OIDC 认证流程完整演示")
    print("=" * 60)
    
    # 演示概念
    demonstrate_oidc_concepts()
    show_oidc_vs_traditional()
    
    print("\n🔧 实际API演示")
    print("=" * 60)
    
    # 创建演示实例
    demo = OIDCDemo()
    
    # 获取可用提供商
    providers = demo.get_available_providers()
    
    if providers and providers.get('providers'):
        # 选择第一个可用提供商进行演示
        provider = providers['providers'][0]
        provider_name = provider['name']
        
        # 模拟OIDC流程
        login_result = demo.simulate_oidc_flow(provider_name)
        
        if login_result:
            print(f"\n💡 在实际应用中，用户会被重定向到:")
            print(f"   {login_result['redirect_url']}")
            print(f"\n   用户在 {provider['display_name']} 完成认证后,")
            print(f"   会被重定向回应用的回调URL")
            
            # 模拟成功的回调（实际中由OIDC提供商处理）
            print(f"\n🔄 模拟成功回调处理...")
            print("   注意：这里模拟的是理想情况，实际需要:")
            print("   1. 正确的授权码")
            print("   2. 有效的session状态")
            print("   3. 配置好的OIDC提供商")
        
        # 演示注销
        demo.demonstrate_logout(provider_name)
    
    else:
        print("\n⚠️  没有配置OIDC提供商")
        print("请设置环境变量以启用OIDC提供商:")
        print("- GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET")
        print("- AZURE_CLIENT_ID & AZURE_CLIENT_SECRET")
        print("- GITHUB_CLIENT_ID & GITHUB_CLIENT_SECRET")
    
    print("\n🎉 演示完成!")
    print("\n📖 更多信息请参考:")
    print("- OIDC设置指南: docs/OIDC_SETUP_GUIDE.md")
    print("- API文档: http://localhost:8000/docs")


if __name__ == "__main__":
    main()