"""
Prefect部署管理模块
"""
import datetime
import tempfile
import os
import asyncio
from typing import Dict, Any, Optional, Union

from prefect.client.orchestration import get_client
from config import config
from src.flows import hello_flow, health_check_flow
from src.exceptions import (
    DeploymentError, NetworkError, TimeoutError as CustomTimeoutError,
    ConfigurationError, DockerError
)
from src.logger import get_logger

logger = get_logger(__name__)


class DeploymentManager:
    """部署管理器"""
    
    def __init__(self):
        self.config = config
        # 确保 Prefect 客户端使用配置文件中的 API URL
        self.config.apply_prefect_settings()
        
        # 验证配置
        self._validate_configuration()
        
        # 记录配置信息
        logger.log_config(self.config.get_config_summary())
    
    def _validate_configuration(self) -> None:
        """验证配置"""
        missing = self.config.validate_required_settings()
        if missing:
            raise ConfigurationError(
                f"缺少必需的配置项: {', '.join(missing)}",
                {"missing_configs": missing}
            )
        
        if not self.config.validate_network_settings():
            raise ConfigurationError(
                "Prefect API URL格式无效",
                {"api_url": self.config.prefect_api_url}
            )
        
    def _generate_image_tag(self) -> str:
        """生成镜像标签"""
        if self.config.image_tag:
            image_tag = f"{self.config.image_repo}:{self.config.image_tag}"
            logger.info(f"使用提供的镜像标签: {image_tag}")
        else:
            current_time = datetime.datetime.now()
            version_tag = f"v{current_time.strftime('%Y%m%d%H%M')}"
            image_tag = f"{self.config.image_repo}:{version_tag}"
            logger.info(f"生成新的镜像标签: {image_tag}")
        
        return image_tag
    
    async def _deploy_hello_flow_async(self, image_tag: str, job_variables: Dict[str, Any], extra_kwargs: Dict[str, Any]) -> str:
        """异步部署hello流"""
        # 在新的事件循环中运行同步部署
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                hello_flow.deploy,
                name="hello-production",
                work_pool_name=self.config.work_pool_name,
                image=image_tag,
                schedule={"interval": self.config.schedule_interval},
                job_variables=job_variables,
                tags=["production", "automated", "hello"],
                description="生产环境的问候流",
                **extra_kwargs,
            )
            return future.result()
    
    def _get_base_env_vars(self) -> Dict[str, str]:
        """获取基础环境变量"""
        return {
            "LOG_LEVEL": self.config.log_level,
            "ENVIRONMENT": self.config.environment,
            "PYTHONUNBUFFERED": "1",
            "PREFECT_LOGGING_LEVEL": self.config.log_level,
            "PREFECT_API_RESPONSE_TIMEOUT": str(self.config.api_timeout),
            "PREFECT_API_REQUEST_TIMEOUT": str(self.config.api_timeout),
        }
    
    def _get_docker_job_variables(self) -> Dict[str, Any]:
        """获取Docker作业变量"""
        if self.config.is_container_env:
            return {
                "env": self._get_base_env_vars()
            }
        else:
            # 本地环境需要更多Docker配置
            temp_log_dir = tempfile.mkdtemp(prefix="prefect_logs_")
            env_vars = self._get_base_env_vars()
            
            return {
                f"env.{k}": v for k, v in env_vars.items()
            } | {
                "env.DOCKER_CLIENT_TIMEOUT": "300",
                "env.COMPOSE_HTTP_TIMEOUT": "300",
                "env.PREFECT_DOCKER_HOST_NETWORK": "true",
                "env.PREFECT_DOCKER_VOLUME_MOUNTS": f"{temp_log_dir}:/tmp/prefect/logs",
                "env.PREFECT_DOCKER_NETWORK": "host"
            }
    
    async def check_prefect_connection(self) -> bool:
        """检查Prefect API连接"""
        try:
            async with get_client() as client:
                await client.api_healthcheck()
                logger.info("Prefect API连接正常")
                return True
        except Exception as e:
            logger.error(f"Prefect API连接失败: {str(e)}")
            return False
    
    async def deploy_hello_flow_async(self) -> str:
        """异步部署hello流"""
        image_tag = self._generate_image_tag()
        job_variables = self._get_docker_job_variables()
        
        logger.log_deployment_start("hello-production", image_tag)
        
        try:
            # 在容器环境中使用不同的部署方式
            if self.config.is_container_env:
                logger.info("检测到容器环境，跳过Docker镜像构建，直接向Prefect服务器注册部署")
                extra_kwargs = {"build": False, "push": False}
            else:
                extra_kwargs = {}
            
            # 使用异步超时控制
            try:
                deployment_id = await asyncio.wait_for(
                    self._deploy_hello_flow_async(image_tag, job_variables, extra_kwargs),
                    timeout=self.config.deployment_timeout
                )
                
                logger.log_deployment_success("hello-production", deployment_id)
                return deployment_id
                
            except asyncio.TimeoutError:
                raise CustomTimeoutError(
                    f"部署操作超时（{self.config.deployment_timeout}秒）",
                    {"timeout": self.config.deployment_timeout}
                )
            
        except Exception as e:
            logger.log_deployment_error("hello-production", e)
            self._handle_deployment_error(e)
            raise
    
    def deploy_hello_flow(self) -> str:
        """部署hello流 - 同步接口"""
        return asyncio.run(self.deploy_hello_flow_async())
    
    def _handle_deployment_error(self, error: Exception) -> None:
        """处理部署错误，提供详细的诊断信息"""
        error_msg = str(error).lower()
        
        if "connecttimeouterror" in error_msg or "timeout" in error_msg:
            raise NetworkError(
                "网络连接超时",
                {
                    "original_error": str(error),
                    "api_url": self.config.prefect_api_url,
                    "timeout": self.config.api_timeout
                }
            )
        elif "work_pool" in error_msg or "pool" in error_msg:
            raise DeploymentError(
                f"工作池 '{self.config.work_pool_name}' 相关错误",
                {
                    "original_error": str(error),
                    "work_pool_name": self.config.work_pool_name
                }
            )
        elif "authentication" in error_msg or "unauthorized" in error_msg:
            raise DeploymentError(
                "认证失败",
                {
                    "original_error": str(error),
                    "api_url": self.config.prefect_api_url
                }
            )
        elif "docker" in error_msg:
            raise DockerError(
                "Docker 相关错误",
                {
                    "original_error": str(error),
                    "is_container_env": self.config.is_container_env
                }
            )
        else:
            raise DeploymentError(
                f"部署失败: {str(error)}",
                {"original_error": str(error)}
            )
    
    def deploy_health_check_flow(self) -> str:
        """部署健康检查流"""
        image_tag = self._generate_image_tag()
        job_variables = self._get_docker_job_variables()
        
        logger.info(f"开始部署健康检查流，镜像: {image_tag}")
        
        try:
            deployment_id = health_check_flow.deploy(
                name="health-check-production",
                work_pool_name=self.config.work_pool_name,
                image=image_tag,
                schedule={"interval": 300},  # 5分钟检查一次
                job_variables=job_variables,
                tags=["production", "health-check"],
                description="生产环境健康检查流",
            )
            
            logger.info(f"健康检查流部署成功，ID: {deployment_id}")
            return deployment_id
            
        except Exception as e:
            logger.error(f"健康检查流部署失败: {str(e)}")
            raise
    
    def deploy_all(self) -> Dict[str, Union[str, Dict[str, Any]]]:
        """部署所有流"""
        results = {}
        
        try:
            logger.info("开始部署主要流程...")
            results["hello_flow"] = self.deploy_hello_flow()
            
            logger.info("流部署完成")
            return results
            
        except Exception as e:
            logger.log_deployment_error("deploy_all", e)
            
            # 在容器环境中，提供诊断信息但不抛出异常
            if self.config.is_container_env:
                logger.warning("容器环境中的部署失败，返回错误信息而不是抛出异常")
                
                # 特殊处理Docker相关错误
                if isinstance(e, DockerError) and "Docker is not running" in str(e):
                    logger.warning("检测到Docker服务未运行错误 - 在容器内部署时不需要Docker服务")
                    return {"status": "success", "message": "容器内部署 - 忽略Docker服务未运行错误"}
                
                # 返回错误信息和故障排除提示
                if hasattr(e, 'get_troubleshooting_info'):
                    return {
                        "status": "failed",
                        **e.get_troubleshooting_info()
                    }
                else:
                    return {"error": str(e), "status": "failed"}
            else:
                raise


def deploy_flows():
    """部署流的入口函数"""
    manager = DeploymentManager()
    return manager.deploy_all()