#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用配置管理
使用Pydantic Settings进行配置管理和验证
"""

import os
import secrets
from typing import List, Optional
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基本信息
    APP_NAME: str = "FastAPI用户服务"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./users.db"
    DATABASE_ECHO: bool = False  # 是否打印SQL语句
    
    # JWT配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 密码配置
    PWD_MIN_LENGTH: int = 8
    PWD_MAX_LENGTH: int = 50
    PWD_REQUIRE_UPPERCASE: bool = True
    PWD_REQUIRE_LOWERCASE: bool = True
    PWD_REQUIRE_NUMBERS: bool = True
    PWD_REQUIRE_SPECIAL: bool = False
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = ["*"]
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]
    
    # 用户名配置
    USERNAME_MIN_LENGTH: int = 3
    USERNAME_MAX_LENGTH: int = 20
    USERNAME_PATTERN: str = r"^[a-zA-Z0-9_-]+$"
    
    # 邮箱配置
    EMAIL_MAX_LENGTH: int = 254
    
    # 速率限制配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1小时
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Redis配置（可选，用于缓存和会话）
    REDIS_URL: Optional[str] = None
    REDIS_EXPIRE: int = 3600
    
    # 邮件配置（可选，用于邮箱验证）
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    
    # 文件上传配置
    UPLOAD_MAX_SIZE: int = 5 * 1024 * 1024  # 5MB
    UPLOAD_ALLOWED_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]
    UPLOAD_PATH: str = "./uploads"
    
    # 安全配置
    ENABLE_REGISTRATION: bool = True
    REQUIRE_EMAIL_VERIFICATION: bool = False
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v):
        """验证SECRET_KEY"""
        if not v:
            return secrets.token_urlsafe(32)
        if len(v) < 32:
            raise ValueError("SECRET_KEY长度至少32个字符")
        return v
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        """验证数据库URL"""
        if not v:
            return "sqlite:///./users.db"
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def validate_allowed_hosts(cls, v):
        """验证允许的主机列表"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def validate_cors_origins(cls, v):
        """验证CORS源列表"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    def validate_token_expire(cls, v):
        """验证Token过期时间"""
        if v <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES必须大于0")
        return v
    
    @validator("PWD_MIN_LENGTH")
    def validate_password_min_length(cls, v):
        """验证密码最小长度"""
        if v < 6:
            raise ValueError("密码最小长度不能少于6个字符")
        return v
    
    @validator("USERNAME_MIN_LENGTH")
    def validate_username_min_length(cls, v):
        """验证用户名最小长度"""
        if v < 3:
            raise ValueError("用户名最小长度不能少于3个字符")
        return v
    
    @property
    def database_url_sync(self) -> str:
        """同步数据库URL"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
        return self.DATABASE_URL
    
    @property
    def database_url_async(self) -> str:
        """异步数据库URL"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        elif self.DATABASE_URL.startswith("sqlite://"):
            return self.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        return self.DATABASE_URL
    
    def get_password_requirements(self) -> dict:
        """获取密码要求"""
        return {
            "min_length": self.PWD_MIN_LENGTH,
            "max_length": self.PWD_MAX_LENGTH,
            "require_uppercase": self.PWD_REQUIRE_UPPERCASE,
            "require_lowercase": self.PWD_REQUIRE_LOWERCASE,
            "require_numbers": self.PWD_REQUIRE_NUMBERS,
            "require_special": self.PWD_REQUIRE_SPECIAL
        }
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.DEBUG
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return not self.DEBUG
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# 创建全局配置实例
settings = Settings()

# 开发环境特殊配置
if settings.is_development():
    settings.DATABASE_ECHO = True
    settings.LOG_LEVEL = "DEBUG"

# 生产环境特殊配置
if settings.is_production():
    # 生产环境必须设置强密钥
    if settings.SECRET_KEY == "your-secret-key-here":
        raise ValueError("生产环境必须设置安全的SECRET_KEY")
    
    # 生产环境关闭调试模式
    settings.DEBUG = False
    
    # 生产环境限制CORS
    if "*" in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS = [
            "yourdomain.com",
            "www.yourdomain.com"
        ]

# 配置验证函数
def validate_config():
    """验证配置完整性"""
    errors = []
    
    # 检查必要配置
    if not settings.SECRET_KEY:
        errors.append("SECRET_KEY未设置")
    
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL未设置")
    
    # 检查密码策略
    if settings.PWD_MIN_LENGTH > settings.PWD_MAX_LENGTH:
        errors.append("密码最小长度不能大于最大长度")
    
    # 检查Token过期时间
    if settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        errors.append("Token过期时间必须大于0")
    
    if errors:
        raise ValueError(f"配置验证失败: {'; '.join(errors)}")

# 打印配置信息（隐藏敏感信息）
def print_config():
    """打印当前配置（用于调试）"""
    print("\n" + "="*50)
    print(f"🚀 {settings.APP_NAME} v{settings.VERSION}")
    print("="*50)
    print(f"📊 调试模式: {settings.DEBUG}")
    print(f"🗄️ 数据库: {settings.DATABASE_URL}")
    print(f"🔐 JWT算法: {settings.ALGORITHM}")
    print(f"⏰ Token过期: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}分钟")
    print(f"🛡️ 密码最小长度: {settings.PWD_MIN_LENGTH}")
    print(f"🌐 允许主机: {settings.ALLOWED_HOSTS}")
    print(f"📝 日志级别: {settings.LOG_LEVEL}")
    print(f"📁 上传路径: {settings.UPLOAD_PATH}")
    print("="*50 + "\n")

if __name__ == "__main__":
    # 验证配置
    try:
        validate_config()
        print("✅ 配置验证通过")
        print_config()
    except ValueError as e:
        print(f"❌ 配置验证失败: {e}")
        exit(1)