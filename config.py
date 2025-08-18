"""
Legacy configuration module for backward compatibility
This module wraps the new configuration system to maintain compatibility
"""
import os
import warnings
from dataclasses import dataclass
from typing import Optional

# Import new configuration system
try:
    from src.config import get_settings
    _new_settings = get_settings()
except ImportError:
    # Fallback if new config is not available
    _new_settings = None


@dataclass
class LegacyConfig:
    """
    Legacy configuration class for backward compatibility
    """
    
    def __init__(self):
        """Initialize with values from new settings or environment"""
        if _new_settings:
            # Use new settings system
            self.prefect_api_url = str(_new_settings.prefect_api_url) if _new_settings.prefect_api_url else os.getenv("PREFECT_API_URL", "http://172.31.0.55:4200/api")
            self.work_pool_name = _new_settings.work_pool_name
            self.image_repo = _new_settings.image_repo
            self.image_tag = _new_settings.image_tag
            self.log_level = _new_settings.log_level.value
            self.environment = _new_settings.environment.value
            self.deploy_mode = _new_settings.deploy_mode
            self.schedule_interval = _new_settings.schedule_interval
            self.api_timeout = _new_settings.api_timeout
            self.deployment_timeout = _new_settings.deployment_timeout
        else:
            # Fallback to environment variables
            self.prefect_api_url = os.getenv("PREFECT_API_URL", "http://172.31.0.55:4200/api")
            self.work_pool_name = os.getenv("WORK_POOL_NAME", "my-docker-pool2")
            self.image_repo = os.getenv("IMAGE_REPO", "ghcr.io/samples28/cicd-example")
            self.image_tag = os.getenv("IMAGE_TAG")
            self.log_level = os.getenv("LOG_LEVEL", "INFO")
            self.environment = os.getenv("ENVIRONMENT", "development")
            self.deploy_mode = os.getenv("DEPLOY_MODE", "false").lower() == "true"
            self.schedule_interval = int(os.getenv("SCHEDULE_INTERVAL", "3600"))
            self.api_timeout = int(os.getenv("API_TIMEOUT", "30"))
            self.deployment_timeout = int(os.getenv("DEPLOYMENT_TIMEOUT", "60"))
    
    @property
    def full_image_name(self) -> str:
        """Get full image name"""
        if self.image_tag:
            return f"{self.image_repo}:{self.image_tag}"
        return self.image_repo
    
    @property
    def is_container_env(self) -> bool:
        """Check if running in container"""
        return os.path.exists("/.dockerenv")
    
    @property
    def is_production(self) -> bool:
        """Check if production environment"""
        return self.environment.lower() == "production"
    
    def apply_prefect_settings(self) -> None:
        """Apply Prefect settings to environment"""
        if self.prefect_api_url:
            os.environ["PREFECT_API_URL"] = self.prefect_api_url
            os.environ["PREFECT_LOGGING_LEVEL"] = self.log_level
    
    def validate_required_settings(self) -> list[str]:
        """Validate required settings"""
        missing = []
        
        if self.deploy_mode:
            if not self.prefect_api_url:
                missing.append("PREFECT_API_URL")
            if not self.work_pool_name:
                missing.append("WORK_POOL_NAME")
            if not self.image_repo:
                missing.append("IMAGE_REPO")
        
        return missing
    
    def get_config_summary(self) -> dict:
        """Get config summary"""
        return {
            "prefect_api_url": self.prefect_api_url,
            "work_pool_name": self.work_pool_name,
            "image_repo": self.image_repo,
            "image_tag": self.image_tag,
            "full_image_name": self.full_image_name,
            "environment": self.environment,
            "deploy_mode": self.deploy_mode,
            "is_container_env": self.is_container_env,
            "is_production": self.is_production,
            "deployment_timeout": self.deployment_timeout,
            "api_timeout": self.api_timeout,
            "schedule_interval": self.schedule_interval,
        }
    
    def print_config_info(self) -> None:
        """Print configuration info"""
        print("=" * 50)
        print("📋 Prefect CI/CD Configuration Info")
        print("=" * 50)
        print(f"🌐 Prefect API URL: {self.prefect_api_url}")
        print(f"🏊 Work Pool Name: {self.work_pool_name}")
        print(f"🐳 Docker Image: {self.full_image_name}")
        print(f"🌍 Environment: {self.environment}")
        print(f"📊 Log Level: {self.log_level}")
        print(f"🚀 Deploy Mode: {'Yes' if self.deploy_mode else 'No'}")
        print(f"📦 Container Environment: {'Yes' if self.is_container_env else 'No'}")
        print(f"⏰ Schedule Interval: {self.schedule_interval} seconds")
        print(f"⏱️  API Timeout: {self.api_timeout} seconds")
        print(f"⏳ Deployment Timeout: {self.deployment_timeout} seconds")
        print("=" * 50)


# Create global config instance
config = LegacyConfig()

# Apply Prefect settings
config.apply_prefect_settings()

# Show deprecation warning
warnings.warn(
    "The config.py module is deprecated. Please use src.config.settings instead.",
    DeprecationWarning,
    stacklevel=2
)