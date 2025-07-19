"""
项目配置文件
集中管理所有配置参数，便于维护和修改
"""

import os
from typing import Dict, Any

class Config:
    """项目配置类"""
    
    # Prefect 配置
    PREFECT_API_URL = os.environ.get("PREFECT_API_URL", "http://localhost:4200/api")
    WORK_POOL_NAME = os.environ.get("WORK_POOL_NAME", "my-docker-pool2")
    
    # Docker 镜像配置
    IMAGE_REPO = os.environ.get("IMAGE_REPO", "ghcr.io/samples28/cicd-example")
    IMAGE_TAG = os.environ.get("IMAGE_TAG", "")
    
    # 部署配置
    DEPLOY_MODE = os.environ.get("DEPLOY_MODE", "false").lower() == "true"
    DEPLOYMENT_NAME = "prod-deployment"
    DEPLOYMENT_DESCRIPTION = "生产环境部署的hello流"
    
    # 调度配置
    SCHEDULE_INTERVAL = 3600  # 秒，每小时执行一次
    
    # 环境配置
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    
    # 超时配置
    DEPLOYMENT_TIMEOUT = 60  # 秒
    API_TIMEOUT = 300  # 秒
    
    # Docker 配置
    DOCKER_NETWORK_MODE = "host"
    DOCKER_CLIENT_TIMEOUT = 300
    COMPOSE_HTTP_TIMEOUT = 300
    
    # 并发配置
    CONCURRENCY_LIMIT = 2
    
    @classmethod
    def get_deployment_tags(cls) -> list:
        """获取部署标签"""
        return ["production", "automated"]
    
    @classmethod
    def get_environment_vars(cls) -> Dict[str, str]:
        """获取环境变量配置"""
        return {
            "LOG_LEVEL": cls.LOG_LEVEL,
            "ENVIRONMENT": cls.ENVIRONMENT,
            "PYTHONUNBUFFERED": "1",
            "PREFECT_LOGGING_LEVEL": cls.LOG_LEVEL,
            "PREFECT_API_RESPONSE_TIMEOUT": str(cls.API_TIMEOUT),
            "PREFECT_API_REQUEST_TIMEOUT": str(cls.API_TIMEOUT),
        }
    
    @classmethod
    def get_docker_job_variables(cls) -> Dict[str, str]:
        """获取Docker作业变量"""
        return {
            "env.LOG_LEVEL": cls.LOG_LEVEL,
            "env.ENVIRONMENT": cls.ENVIRONMENT,
            "env.PYTHONUNBUFFERED": "1",
            "env.DOCKER_CLIENT_TIMEOUT": str(cls.DOCKER_CLIENT_TIMEOUT),
            "env.COMPOSE_HTTP_TIMEOUT": str(cls.COMPOSE_HTTP_TIMEOUT),
            "env.PREFECT_LOGGING_LEVEL": cls.LOG_LEVEL,
            "env.PREFECT_API_RESPONSE_TIMEOUT": str(cls.API_TIMEOUT),
            "env.PREFECT_API_REQUEST_TIMEOUT": str(cls.API_TIMEOUT),
            "env.PREFECT_DOCKER_HOST_NETWORK": "true",
            "env.PREFECT_DOCKER_NETWORK": cls.DOCKER_NETWORK_MODE
        }
    
    @classmethod
    def get_schedule_config(cls) -> Dict[str, Any]:
        """获取调度配置"""
        return {"interval": cls.SCHEDULE_INTERVAL}
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置的有效性"""
        required_vars = [
            "PREFECT_API_URL",
            "WORK_POOL_NAME",
            "IMAGE_REPO"
        ]
        
        for var in required_vars:
            if not getattr(cls, var):
                print(f"错误: 缺少必需的配置 {var}")
                return False
        
        return True

# 创建全局配置实例
config = Config()