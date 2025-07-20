from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    database_url: str = "postgresql://user:password@localhost/userauth"
    
    # JWT settings (仍然用于内部token管理)
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Client Authentication settings
    client_token_expire_minutes: int = 60  # 客户端令牌过期时间
    api_key_expire_days: int = 365  # API密钥过期天数
    max_clients_per_user: int = 10  # 每个用户最大客户端数量
    
    # Security settings
    bcrypt_rounds: int = 12
    
    # Application settings
    app_name: str = "User Auth API"
    debug: bool = True
    base_url: str = "http://localhost:8000"
    
    # Rate limiting settings
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst: int = 20
    
    # OIDC Provider Settings (保留现有OIDC配置)
    # Google OAuth 2.0 / OIDC
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    # Microsoft Azure AD
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = "common"  # 或特定租户ID
    
    # GitHub OAuth 2.0
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    
    # 自定义OIDC提供商
    custom_oidc_name: Optional[str] = None
    custom_oidc_client_id: Optional[str] = None
    custom_oidc_client_secret: Optional[str] = None
    custom_oidc_discovery_url: Optional[str] = None
    custom_oidc_scopes: Optional[list[str]] = None
    
    # Session settings (OIDC需要session支持)
    session_secret_key: str = "session-secret-key-change-this"
    session_max_age: int = 3600  # 1 hour
    
    # OIDC特定设置
    oidc_auto_register: bool = True  # 是否自动注册OIDC用户
    oidc_update_user_info: bool = True  # 是否更新用户信息
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()