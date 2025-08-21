"""
Prefect部署管理模块
"""
import datetime
import logging
import tempfile
import os
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from prefect.client.orchestration import get_client
from config import config
from src.flows import hello_flow, health_check_flow, process_pdf_flow

logger = logging.getLogger(__name__)


class DeploymentManager:
    """部署管理器"""
    
    def __init__(self):
        self.config = config
        # 确保 Prefect 客户端使用配置文件中的 API URL
        self.config.apply_prefect_settings()
        
        # 打印配置信息
        if logger.isEnabledFor(logging.INFO):
            self.config.print_config_info()
        
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
    
    def _deploy_flow(self, flow_to_deploy, deployment_config: Dict[str, Any]) -> str:
        """通用部署函数"""
        image_tag = self._generate_image_tag()
        job_variables = self._get_docker_job_variables()

        flow_name = deployment_config.get("name", flow_to_deploy.name)
        logger.info(f"开始部署 '{flow_name}'，镜像: {image_tag}")
        logger.info(f"工作池: {self.config.work_pool_name}")

        try:
            extra_kwargs = {}
            if self.config.is_container_env:
                logger.info("检测到容器环境，跳过Docker镜像构建和推送")
                extra_kwargs = {"build": False, "push": False}

            def _do_deploy() -> str:
                return flow_to_deploy.deploy(
                    name=deployment_config.get("name"),
                    work_pool_name=self.config.work_pool_name,
                    image=image_tag,
                    schedule=deployment_config.get("schedule"),
                    job_variables=job_variables,
                    tags=deployment_config.get("tags", []),
                    description=deployment_config.get("description", ""),
                    **extra_kwargs,
                )

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_do_deploy)
                try:
                    deployment_id = future.result(timeout=self.config.deployment_timeout)
                except FuturesTimeoutError:
                    logger.error(f"部署 '{flow_name}' 超时 ({self.config.deployment_timeout}秒)")
                    raise TimeoutError(f"部署 '{flow_name}' 超时")

            logger.info(f"'{flow_name}' 部署成功，ID: {deployment_id}")
            return deployment_id

        except Exception as e:
            logger.error(f"'{flow_name}' 部署失败: {str(e)}")
            self._handle_deployment_error(e)
            raise

    def _handle_deployment_error(self, e: Exception):
        """统一处理部署错误"""
        error_msg = str(e).lower()
        if "connecttimeouterror" in error_msg or "timeout" in error_msg:
            logger.error("🌐 网络连接超时")
            logger.info("💡 解决方案: 检查 Prefect API 服务器状态、网络连接和 API_TIMEOUT 配置")
        elif "work_pool" in error_msg or "pool" in error_msg:
            logger.error(f"🏊 工作池 '{self.config.work_pool_name}' 相关错误")
            logger.info("💡 解决方案: 确认工作池存在且名称正确")
        elif "authentication" in error_msg or "unauthorized" in error_msg:
            logger.error("🔐 认证失败")
            logger.info("💡 解决方案: 检查 API 密钥和用户权限")
        elif "docker" in error_msg:
            logger.error("🐳 Docker 相关错误")
            logger.info("💡 解决方案: 检查 Docker 服务是否运行以及相关权限")
        else:
            logger.error("❌ 未知错误类型")
            logger.info("💡 建议: 检查完整的错误日志和所有配置项")

    def deploy_all(self) -> Dict[str, Any]:
        """部署所有已定义的流"""
        flows_to_deploy = [
            {
                "flow": hello_flow,
                "config": {
                    "name": "hello-production",
                    "schedule": {"interval": self.config.schedule_interval},
                    "tags": ["production", "automated", "hello"],
                    "description": "生产环境的问候流",
                },
            },
            {
                "flow": health_check_flow,
                "config": {
                    "name": "health-check-production",
                    "schedule": {"interval": 300},
                    "tags": ["production", "health-check"],
                    "description": "生产环境健康检查流",
                },
            },
            {
                "flow": process_pdf_flow,
                "config": {
                    "name": "process-pdf-production",
                    "schedule": None,  # 按需触发，不设定时调度
                    "tags": ["production", "pdf", "processing"],
                    "description": "PDF文件处理工作流",
                },
            },
        ]

        results = {}
        logger.info("开始部署所有流程...")

        for item in flows_to_deploy:
            flow = item["flow"]
            config = item["config"]
            flow_name = config.get("name", flow.name)
            try:
                deployment_id = self._deploy_flow(flow, config)
                results[flow_name] = {"status": "success", "id": deployment_id}
            except Exception as e:
                results[flow_name] = {"status": "failed", "error": str(e)}
                if not self.config.is_container_env:
                    # 在本地环境中，遇到第一个错误就停止
                    logger.error("本地部署失败，终止部署流程。")
                    raise

        logger.info("所有流程部署完成。")
        return results


def deploy_flows():
    """部署流的入口函数"""
    manager = DeploymentManager()
    return manager.deploy_all()
