"""
OIDC (OpenID Connect) Configuration
支持多种OIDC提供商的配置
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from .config import settings


class OIDCProviderConfig(BaseModel):
    """OIDC提供商配置"""
    name: str
    client_id: str
    client_secret: str
    discovery_url: str
    scopes: list[str] = ["openid", "profile", "email"]
    redirect_uri: str
    post_logout_redirect_uri: Optional[str] = None
    
    # 可选的直接端点配置 (如果discovery不可用)
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    issuer: Optional[str] = None


class OIDCSettings:
    """OIDC设置管理"""
    
    def __init__(self):
        self.providers: Dict[str, OIDCProviderConfig] = {}
        self._load_providers()
    
    def _load_providers(self):
        """加载OIDC提供商配置"""
        
        # Google OIDC配置
        if settings.google_client_id and settings.google_client_secret:
            self.providers["google"] = OIDCProviderConfig(
                name="Google",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                discovery_url="https://accounts.google.com/.well-known/openid_configuration",
                scopes=["openid", "profile", "email"],
                redirect_uri=f"{settings.base_url}/auth/callback/google",
                post_logout_redirect_uri=f"{settings.base_url}/logout"
            )
        
        # Microsoft Azure AD配置
        if settings.azure_client_id and settings.azure_client_secret:
            tenant_id = settings.azure_tenant_id or "common"
            self.providers["azure"] = OIDCProviderConfig(
                name="Microsoft",
                client_id=settings.azure_client_id,
                client_secret=settings.azure_client_secret,
                discovery_url=f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid_configuration",
                scopes=["openid", "profile", "email"],
                redirect_uri=f"{settings.base_url}/auth/callback/azure",
                post_logout_redirect_uri=f"{settings.base_url}/logout"
            )
        
        # GitHub OAuth配置 (不是标准OIDC，但使用OAuth 2.0)
        if settings.github_client_id and settings.github_client_secret:
            self.providers["github"] = OIDCProviderConfig(
                name="GitHub",
                client_id=settings.github_client_id,
                client_secret=settings.github_client_secret,
                discovery_url="",  # GitHub不支持discovery
                scopes=["user:email"],
                redirect_uri=f"{settings.base_url}/auth/callback/github",
                authorization_endpoint="https://github.com/login/oauth/authorize",
                token_endpoint="https://github.com/login/oauth/access_token",
                userinfo_endpoint="https://api.github.com/user"
            )
        
        # 自定义OIDC提供商配置
        if settings.custom_oidc_discovery_url:
            self.providers["custom"] = OIDCProviderConfig(
                name=settings.custom_oidc_name or "Custom OIDC",
                client_id=settings.custom_oidc_client_id,
                client_secret=settings.custom_oidc_client_secret,
                discovery_url=settings.custom_oidc_discovery_url,
                scopes=settings.custom_oidc_scopes or ["openid", "profile", "email"],
                redirect_uri=f"{settings.base_url}/auth/callback/custom"
            )
    
    def get_provider(self, provider_name: str) -> Optional[OIDCProviderConfig]:
        """获取指定的OIDC提供商配置"""
        return self.providers.get(provider_name)
    
    def get_available_providers(self) -> list[str]:
        """获取可用的OIDC提供商列表"""
        return list(self.providers.keys())
    
    def is_provider_enabled(self, provider_name: str) -> bool:
        """检查指定提供商是否已启用"""
        return provider_name in self.providers


# OIDC相关的常量
OIDC_STATE_LENGTH = 32
OIDC_NONCE_LENGTH = 32
OIDC_CODE_VERIFIER_LENGTH = 128

# Session keys
SESSION_STATE_KEY = "oidc_state"
SESSION_NONCE_KEY = "oidc_nonce"
SESSION_CODE_VERIFIER_KEY = "oidc_code_verifier"
SESSION_PROVIDER_KEY = "oidc_provider"

# 创建全局OIDC设置实例
oidc_settings = OIDCSettings()