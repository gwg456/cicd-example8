"""
配置管理模块

统一管理应用的所有配置项，支持通过环境变量进行配置。
配置项会自动应用到相应的系统组件中。
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()


@dataclass
class Config:
    """
    应用配置类
    
    所有配置项都支持通过环境变量设置，提供合理的默认值。
    配置会在导入时自动应用到相应的系统组件。
    """
    
    # Prefect配置
    prefect_api_url: str = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")
    work_pool_name: str = os.getenv("WORK_POOL_NAME", "my-docker-pool2")
    
    # Docker配置
    image_repo: str = os.getenv("IMAGE_REPO", "ghcr.io/samples28/cicd-example")
    image_tag: Optional[str] = os.getenv("IMAGE_TAG")
    
    # 应用配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    environment: str = os.getenv("ENVIRONMENT", "development")
    deploy_mode: bool = os.getenv("DEPLOY_MODE", "false").lower() == "true"
    
    # 调度配置
    schedule_interval: int = int(os.getenv("SCHEDULE_INTERVAL", "3600"))  # 默认1小时
    
    # 超时配置（统一）
    api_timeout: int = int(os.getenv("PREFECT_API_TIMEOUT", os.getenv("API_TIMEOUT", "300")))  # API请求超时时间（秒）
    deployment_timeout: int = int(os.getenv("DEPLOYMENT_TIMEOUT", "60"))  # 部署操作超时时间（秒）
    
    @property
    def full_image_name(self) -> str:
        """获取完整的镜像名称"""
        if self.image_tag:
            return f"{self.image_repo}:{self.image_tag}"
        return self.image_repo
    
    @property
    def is_container_env(self) -> bool:
        """检查是否在容器环境中运行"""
        return os.path.exists("/.dockerenv")
    
    @property
    def is_production(self) -> bool:
        """检查是否为生产环境"""
        return self.environment.lower() == "production"
    
    def apply_prefect_settings(self) -> None:
        """应用 Prefect 相关的环境变量设置"""
        if self.prefect_api_url:
            os.environ["PREFECT_API_URL"] = self.prefect_api_url
            # 确保其他 Prefect 相关的环境变量也被设置
            os.environ["PREFECT_LOGGING_LEVEL"] = self.log_level
    
    def validate_required_settings(self) -> list[str]:
        """
        验证必需的配置项
        
        Returns:
            list[str]: 缺失的配置项列表
        """
        missing = []
        
        if self.deploy_mode:
            if not self.prefect_api_url:
                missing.append("PREFECT_API_URL")
            if not self.work_pool_name:
                missing.append("WORK_POOL_NAME")
            if not self.image_repo:
                missing.append("IMAGE_REPO")
        
        # 验证超时配置的合理性
        if self.api_timeout <= 0:
            missing.append("PREFECT_API_TIMEOUT (必须大于0)")
        if self.deployment_timeout <= 0:
            missing.append("DEPLOYMENT_TIMEOUT (必须大于0)")
        
        return missing
    
    def get_config_summary(self) -> dict:
        """获取配置摘要信息"""
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
        """打印配置信息到控制台"""
        print("=" * 50)
        print("📋 Prefect CI/CD 配置信息")
        print("=" * 50)
        print(f"🌐 Prefect API URL: {self.prefect_api_url}")
        print(f"🏊 工作池名称: {self.work_pool_name}")
        print(f"🐳 Docker 镜像: {self.full_image_name}")
        print(f"🌍 运行环境: {self.environment}")
        print(f"📊 日志级别: {self.log_level}")
        print(f"🚀 部署模式: {'是' if self.deploy_mode else '否'}")
        print(f"📦 容器环境: {'是' if self.is_container_env else '否'}")
        print(f"⏰ 调度间隔: {self.schedule_interval}秒")
        print(f"⏱️  API超时: {self.api_timeout}秒")
        print(f"⏳ 部署超时: {self.deployment_timeout}秒")
        print("=" * 50)


# 全局配置实例
config = Config()

# 自动应用 Prefect 设置
config.apply_prefect_settings()