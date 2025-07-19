from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    database_url: str = "postgresql://user:password@localhost/userauth"
    
    # JWT settings
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Security settings
    bcrypt_rounds: int = 12
    
    # Application settings
    app_name: str = "User Auth API"
    debug: bool = True
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()