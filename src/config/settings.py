"""
Production-grade configuration management with Pydantic
"""
import os
from enum import Enum
from functools import lru_cache
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field, validator, SecretStr
from pydantic.networks import HttpUrl
import logging

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    Application settings with validation and type checking
    """
    
    # Application settings
    app_name: str = Field(default="prefect-cicd", description="Application name")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Current environment"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    
    # Prefect configuration
    prefect_api_url: Optional[HttpUrl] = Field(
        default=None,
        description="Prefect API URL",
        env="PREFECT_API_URL"
    )
    prefect_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Prefect API key for authentication",
        env="PREFECT_API_KEY"
    )
    work_pool_name: str = Field(
        default="default-pool",
        description="Prefect work pool name"
    )
    
    # Docker configuration
    image_repo: str = Field(
        default="ghcr.io/samples28/cicd-example",
        description="Docker image repository"
    )
    image_tag: Optional[str] = Field(
        default=None,
        description="Docker image tag"
    )
    docker_registry_url: Optional[HttpUrl] = Field(
        default=None,
        description="Docker registry URL",
        env="DOCKER_REGISTRY_URL"
    )
    docker_registry_username: Optional[str] = Field(
        default=None,
        description="Docker registry username",
        env="DOCKER_REGISTRY_USERNAME"
    )
    docker_registry_password: Optional[SecretStr] = Field(
        default=None,
        description="Docker registry password",
        env="DOCKER_REGISTRY_PASSWORD"
    )
    
    # Deployment configuration
    deploy_mode: bool = Field(
        default=False,
        description="Enable deployment mode"
    )
    schedule_interval: int = Field(
        default=3600,
        description="Schedule interval in seconds",
        ge=60,  # Minimum 1 minute
        le=86400  # Maximum 1 day
    )
    
    # Timeout configuration
    api_timeout: int = Field(
        default=30,
        description="API request timeout in seconds",
        ge=5,
        le=300
    )
    deployment_timeout: int = Field(
        default=60,
        description="Deployment operation timeout in seconds",
        ge=30,
        le=600
    )
    task_timeout: int = Field(
        default=300,
        description="Task execution timeout in seconds",
        ge=60,
        le=3600
    )
    
    # Performance configuration
    max_workers: int = Field(
        default=4,
        description="Maximum number of worker threads",
        ge=1,
        le=32
    )
    connection_pool_size: int = Field(
        default=10,
        description="Database connection pool size",
        ge=1,
        le=100
    )
    cache_ttl: int = Field(
        default=300,
        description="Cache TTL in seconds",
        ge=0
    )
    
    # Monitoring configuration
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    metrics_port: int = Field(
        default=8000,
        description="Metrics server port",
        ge=1024,
        le=65535
    )
    enable_tracing: bool = Field(
        default=False,
        description="Enable distributed tracing"
    )
    tracing_endpoint: Optional[HttpUrl] = Field(
        default=None,
        description="Tracing collector endpoint"
    )
    
    # Security configuration
    enable_auth: bool = Field(
        default=True,
        description="Enable authentication"
    )
    jwt_secret_key: Optional[SecretStr] = Field(
        default=None,
        description="JWT secret key for token signing",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    jwt_expiration_minutes: int = Field(
        default=30,
        description="JWT token expiration time in minutes",
        ge=5,
        le=1440  # Max 24 hours
    )
    
    # Retry configuration
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries",
        ge=0,
        le=10
    )
    retry_delay: float = Field(
        default=1.0,
        description="Initial retry delay in seconds",
        ge=0.1,
        le=60
    )
    retry_backoff_factor: float = Field(
        default=2.0,
        description="Retry backoff factor",
        ge=1.0,
        le=10.0
    )
    
    @validator("environment", pre=True)
    def validate_environment(cls, v):
        """Validate and normalize environment value"""
        if isinstance(v, str):
            v = v.lower()
            if v not in [e.value for e in Environment]:
                logger.warning(f"Invalid environment '{v}', defaulting to 'development'")
                return Environment.DEVELOPMENT
        return v
    
    @validator("prefect_api_url", pre=True)
    def validate_prefect_api_url(cls, v):
        """Validate Prefect API URL"""
        if v and isinstance(v, str):
            # Ensure URL has proper scheme
            if not v.startswith(("http://", "https://")):
                v = f"http://{v}"
            # Remove trailing slashes
            v = v.rstrip("/")
        return v
    
    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v, values):
        """Ensure JWT secret is set in production"""
        if values.get("enable_auth") and values.get("environment") == Environment.PRODUCTION:
            if not v:
                raise ValueError("JWT_SECRET_KEY must be set in production when auth is enabled")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_container_env(self) -> bool:
        """Check if running in container"""
        return os.path.exists("/.dockerenv") or os.environ.get("CONTAINER_ENV") == "true"
    
    @property
    def full_image_name(self) -> str:
        """Get full Docker image name with tag"""
        if self.image_tag:
            return f"{self.image_repo}:{self.image_tag}"
        return f"{self.image_repo}:latest"
    
    def get_prefect_settings(self) -> Dict[str, Any]:
        """Get Prefect-specific settings"""
        settings = {
            "PREFECT_API_URL": str(self.prefect_api_url) if self.prefect_api_url else None,
            "PREFECT_LOGGING_LEVEL": self.log_level.value,
        }
        
        if self.prefect_api_key:
            settings["PREFECT_API_KEY"] = self.prefect_api_key.get_secret_value()
        
        return {k: v for k, v in settings.items() if v is not None}
    
    def get_docker_job_variables(self) -> Dict[str, Any]:
        """Get Docker job variables for Prefect deployments"""
        env_vars = {
            "LOG_LEVEL": self.log_level.value,
            "ENVIRONMENT": self.environment.value,
            "PYTHONUNBUFFERED": "1",
            "PREFECT_LOGGING_LEVEL": self.log_level.value,
        }
        
        if self.is_container_env:
            return {"env": env_vars}
        else:
            # Local environment needs additional Docker configuration
            return {
                f"env.{k}": v for k, v in env_vars.items()
            } | {
                "env.DOCKER_CLIENT_TIMEOUT": str(self.api_timeout),
                "env.COMPOSE_HTTP_TIMEOUT": str(self.api_timeout),
            }
    
    def validate_deployment_requirements(self) -> list[str]:
        """
        Validate required settings for deployment
        
        Returns:
            List of missing or invalid configuration items
        """
        issues = []
        
        if self.deploy_mode:
            if not self.prefect_api_url:
                issues.append("PREFECT_API_URL is required for deployment")
            
            if not self.work_pool_name:
                issues.append("WORK_POOL_NAME is required for deployment")
            
            if not self.image_repo:
                issues.append("IMAGE_REPO is required for deployment")
            
            if self.is_production and not self.prefect_api_key:
                issues.append("PREFECT_API_KEY is required in production")
        
        return issues
    
    def print_config_summary(self) -> None:
        """Print configuration summary"""
        print("=" * 60)
        print("📋 Configuration Summary")
        print("=" * 60)
        print(f"🌍 Environment: {self.environment.value}")
        print(f"🚀 Deploy Mode: {'Enabled' if self.deploy_mode else 'Disabled'}")
        print(f"📊 Log Level: {self.log_level.value}")
        print(f"🐳 Docker Image: {self.full_image_name}")
        
        if self.prefect_api_url:
            print(f"🌐 Prefect API: {self.prefect_api_url}")
            print(f"🏊 Work Pool: {self.work_pool_name}")
        
        print(f"⏰ Schedule Interval: {self.schedule_interval}s")
        print(f"⏱️  API Timeout: {self.api_timeout}s")
        print(f"📦 Container Environment: {'Yes' if self.is_container_env else 'No'}")
        
        if self.enable_metrics:
            print(f"📈 Metrics: Enabled on port {self.metrics_port}")
        
        if self.enable_tracing:
            print(f"🔍 Tracing: Enabled")
        
        print("=" * 60)
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow extra fields for forward compatibility
        extra = "ignore"
        
        # Use enum values for JSON serialization
        use_enum_values = True
        
        # Validate assignment after initialization
        validate_assignment = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    
    This function uses LRU cache to ensure we only create one
    Settings instance throughout the application lifecycle.
    """
    return Settings()


# Create a global settings instance for backward compatibility
settings = get_settings()