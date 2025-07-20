"""
OIDC (OpenID Connect) Authentication Service
实现OIDC认证流程的核心服务
"""

import secrets
import hashlib
import base64
import urllib.parse
from typing import Dict, Any, Optional, Tuple
from authlib.integrations.requests_client import OAuth2Session
from authlib.oidc.core import CodeIDToken
from authlib.jose import jwt
import requests

from .oidc_config import oidc_settings, OIDCProviderConfig
from .config import settings


class OIDCService:
    """OIDC认证服务"""
    
    def __init__(self):
        self._discovery_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_discovery_document(self, provider_config: OIDCProviderConfig) -> Dict[str, Any]:
        """获取OIDC发现文档"""
        if not provider_config.discovery_url:
            # 对于不支持discovery的提供商（如GitHub），返回手动配置
            return {
                "authorization_endpoint": provider_config.authorization_endpoint,
                "token_endpoint": provider_config.token_endpoint,
                "userinfo_endpoint": provider_config.userinfo_endpoint,
                "jwks_uri": provider_config.jwks_uri,
                "issuer": provider_config.issuer
            }
        
        # 检查缓存
        if provider_config.discovery_url in self._discovery_cache:
            return self._discovery_cache[provider_config.discovery_url]
        
        try:
            response = requests.get(provider_config.discovery_url, timeout=10)
            response.raise_for_status()
            discovery_doc = response.json()
            
            # 缓存发现文档
            self._discovery_cache[provider_config.discovery_url] = discovery_doc
            return discovery_doc
            
        except Exception as e:
            raise Exception(f"Failed to fetch discovery document: {e}")
    
    def generate_state(self) -> str:
        """生成随机state参数"""
        return secrets.token_urlsafe(32)
    
    def generate_nonce(self) -> str:
        """生成随机nonce参数"""
        return secrets.token_urlsafe(32)
    
    def generate_code_verifier(self) -> str:
        """生成PKCE code verifier"""
        return secrets.token_urlsafe(128)[:128]
    
    def generate_code_challenge(self, code_verifier: str) -> str:
        """生成PKCE code challenge"""
        code_sha = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(code_sha).decode('utf-8').rstrip('=')
    
    def build_authorization_url(
        self, 
        provider_name: str, 
        state: str, 
        nonce: str,
        code_verifier: Optional[str] = None
    ) -> str:
        """构建授权URL"""
        provider_config = oidc_settings.get_provider(provider_name)
        if not provider_config:
            raise ValueError(f"Provider {provider_name} not configured")
        
        discovery_doc = self.get_discovery_document(provider_config)
        auth_endpoint = discovery_doc.get("authorization_endpoint")
        
        if not auth_endpoint:
            raise ValueError(f"Authorization endpoint not found for provider {provider_name}")
        
        # 构建授权参数
        params = {
            "response_type": "code",
            "client_id": provider_config.client_id,
            "redirect_uri": provider_config.redirect_uri,
            "scope": " ".join(provider_config.scopes),
            "state": state,
        }
        
        # 如果是OIDC提供商，添加nonce
        if "openid" in provider_config.scopes:
            params["nonce"] = nonce
        
        # 如果支持PKCE，添加code challenge
        if code_verifier:
            code_challenge = self.generate_code_challenge(code_verifier)
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        
        # 构建完整URL
        auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"
        return auth_url
    
    def exchange_code_for_tokens(
        self, 
        provider_name: str, 
        code: str, 
        state: str,
        code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """用授权码换取tokens"""
        provider_config = oidc_settings.get_provider(provider_name)
        if not provider_config:
            raise ValueError(f"Provider {provider_name} not configured")
        
        discovery_doc = self.get_discovery_document(provider_config)
        token_endpoint = discovery_doc.get("token_endpoint")
        
        if not token_endpoint:
            raise ValueError(f"Token endpoint not found for provider {provider_name}")
        
        # 构建token请求参数
        token_data = {
            "grant_type": "authorization_code",
            "client_id": provider_config.client_id,
            "client_secret": provider_config.client_secret,
            "code": code,
            "redirect_uri": provider_config.redirect_uri,
        }
        
        # 如果使用PKCE，添加code verifier
        if code_verifier:
            token_data["code_verifier"] = code_verifier
        
        try:
            response = requests.post(
                token_endpoint,
                data=token_data,
                headers={"Accept": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            raise Exception(f"Failed to exchange code for tokens: {e}")
    
    def get_userinfo(self, provider_name: str, access_token: str) -> Dict[str, Any]:
        """获取用户信息"""
        provider_config = oidc_settings.get_provider(provider_name)
        if not provider_config:
            raise ValueError(f"Provider {provider_name} not configured")
        
        discovery_doc = self.get_discovery_document(provider_config)
        userinfo_endpoint = discovery_doc.get("userinfo_endpoint")
        
        if not userinfo_endpoint:
            raise ValueError(f"Userinfo endpoint not found for provider {provider_name}")
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(userinfo_endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            raise Exception(f"Failed to get user info: {e}")
    
    def verify_id_token(
        self, 
        provider_name: str, 
        id_token: str, 
        nonce: str
    ) -> Dict[str, Any]:
        """验证ID Token"""
        provider_config = oidc_settings.get_provider(provider_name)
        if not provider_config:
            raise ValueError(f"Provider {provider_name} not configured")
        
        discovery_doc = self.get_discovery_document(provider_config)
        jwks_uri = discovery_doc.get("jwks_uri")
        issuer = discovery_doc.get("issuer")
        
        if not jwks_uri or not issuer:
            raise ValueError(f"JWKS URI or issuer not found for provider {provider_name}")
        
        try:
            # 获取公钥
            jwks_response = requests.get(jwks_uri, timeout=10)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()
            
            # 验证ID Token
            claims = jwt.decode(
                id_token,
                jwks,
                claims_options={
                    "iss": {"essential": True, "value": issuer},
                    "aud": {"essential": True, "value": provider_config.client_id},
                    "nonce": {"essential": True, "value": nonce}
                }
            )
            
            return claims
            
        except Exception as e:
            raise Exception(f"Failed to verify ID token: {e}")
    
    def normalize_user_info(self, provider_name: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """标准化用户信息格式"""
        # 不同提供商返回的用户信息格式可能不同，这里进行标准化
        normalized = {
            "provider": provider_name,
            "provider_user_id": None,
            "email": None,
            "email_verified": False,
            "name": None,
            "given_name": None,
            "family_name": None,
            "picture": None,
            "locale": None,
            "raw_user_info": user_info
        }
        
        if provider_name == "google":
            normalized.update({
                "provider_user_id": user_info.get("sub"),
                "email": user_info.get("email"),
                "email_verified": user_info.get("email_verified", False),
                "name": user_info.get("name"),
                "given_name": user_info.get("given_name"),
                "family_name": user_info.get("family_name"),
                "picture": user_info.get("picture"),
                "locale": user_info.get("locale")
            })
        
        elif provider_name == "azure":
            normalized.update({
                "provider_user_id": user_info.get("oid") or user_info.get("sub"),
                "email": user_info.get("email") or user_info.get("preferred_username"),
                "email_verified": user_info.get("email_verified", True),  # Azure一般已验证
                "name": user_info.get("name"),
                "given_name": user_info.get("given_name"),
                "family_name": user_info.get("family_name"),
                "picture": None,  # Azure AD不提供picture
                "locale": user_info.get("locale")
            })
        
        elif provider_name == "github":
            # GitHub需要额外获取邮箱信息
            normalized.update({
                "provider_user_id": str(user_info.get("id")),
                "email": user_info.get("email"),
                "email_verified": True if user_info.get("email") else False,
                "name": user_info.get("name") or user_info.get("login"),
                "given_name": None,  # GitHub不提供
                "family_name": None,  # GitHub不提供
                "picture": user_info.get("avatar_url"),
                "locale": None
            })
        
        else:
            # 自定义提供商，使用标准OIDC字段
            normalized.update({
                "provider_user_id": user_info.get("sub"),
                "email": user_info.get("email"),
                "email_verified": user_info.get("email_verified", False),
                "name": user_info.get("name"),
                "given_name": user_info.get("given_name"),
                "family_name": user_info.get("family_name"),
                "picture": user_info.get("picture"),
                "locale": user_info.get("locale")
            })
        
        return normalized
    
    def build_logout_url(self, provider_name: str, id_token_hint: Optional[str] = None) -> Optional[str]:
        """构建注销URL"""
        provider_config = oidc_settings.get_provider(provider_name)
        if not provider_config:
            return None
        
        try:
            discovery_doc = self.get_discovery_document(provider_config)
            end_session_endpoint = discovery_doc.get("end_session_endpoint")
            
            if not end_session_endpoint:
                return None
            
            params = {}
            if id_token_hint:
                params["id_token_hint"] = id_token_hint
            
            if provider_config.post_logout_redirect_uri:
                params["post_logout_redirect_uri"] = provider_config.post_logout_redirect_uri
            
            if params:
                return f"{end_session_endpoint}?{urllib.parse.urlencode(params)}"
            else:
                return end_session_endpoint
                
        except Exception:
            return None


# 创建全局OIDC服务实例
oidc_service = OIDCService()