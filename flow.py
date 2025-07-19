import time
import os
import datetime
import logging
import tempfile
from prefect import flow
from config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@flow(log_prints=True)
def hello():
    """简单的问候工作流，用于演示 Prefect 部署"""
    print("Hello World! 2025 - This run was scheduled via Interval!")
    time.sleep(20)

def deploy_flow():
    """部署工作流到 Prefect 服务器"""
    try:
        # 验证配置
        if not config.validate_config():
            raise ValueError("配置验证失败")
        
        # 使用环境变量中的镜像标签（如果存在），否则生成一个新的标签
        image_tag = ""
        if config.IMAGE_TAG:
            image_tag = f"{config.IMAGE_REPO}:{config.IMAGE_TAG}"
            logger.info(f"使用GitHub Actions提供的镜像标签: {image_tag}")
        else:
            current_time = datetime.datetime.now()
            version_tag = f"v{current_time.strftime('%Y%m%d%H%M')}"
            image_tag = f"{config.IMAGE_REPO}:{version_tag}"
            logger.info(f"本地生成镜像标签: {image_tag}")
        
        print(f"正在部署镜像: {image_tag}")
        
        # 检查是否在容器内部署
        in_container = os.path.exists("/.dockerenv")
        
        if in_container:
            _deploy_in_container(image_tag)
        else:
            _deploy_locally(image_tag)
        
        print(f"部署已完成，版本: {image_tag}")
        
        if not config.IMAGE_TAG:
            print("注意: 部署前，请确保您的Docker镜像已构建并推送:")
            print(f"  docker build -t {image_tag} .")
            print(f"  docker push {image_tag}")
        
    except Exception as e:
        logger.error(f"部署过程中发生错误: {str(e)}")
        raise

def _deploy_in_container(image_tag):
    """在容器内部署工作流"""
    # 使用配置中的环境变量
    env_vars = config.get_environment_vars()
    
    # 尝试从不同路径导入Docker容器基础设施
    try:
        from prefect_docker.containers import DockerContainer
        docker_infrastructure = DockerContainer(
            image=image_tag,
            env=env_vars,
            network_mode="host",
        )
        logger.info("成功导入DockerContainer")
    except ImportError:
        logger.warning("无法导入DockerContainer，使用默认基础设施配置")
        docker_infrastructure = None
    
    import signal
    
    # 定义超时处理函数
    def timeout_handler(signum, frame):
        logger.error("部署操作超时，可能是网络问题或Prefect服务器无响应")
        raise TimeoutError("部署操作超时")
    
            # 设置超时
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(config.DEPLOYMENT_TIMEOUT)
    
    try:
        logger.info("开始部署流程...")
        
        # 使用新的deploy方法，根据是否有docker_infrastructure决定参数
        if docker_infrastructure:
            logger.info("使用DockerContainer基础设施进行部署")
            deployment_id = hello.deploy(
                name=config.DEPLOYMENT_NAME,
                work_pool_name=config.WORK_POOL_NAME,
                infrastructure=docker_infrastructure,
                schedule=config.get_schedule_config(),
                tags=config.get_deployment_tags(),
                description=config.DEPLOYMENT_DESCRIPTION,
            )
        else:
            logger.info("使用直接image参数进行部署")
            _deploy_with_basic_config(image_tag)
        
        # 取消超时
        signal.alarm(0)
        
    except Exception as e:
        # 取消超时
        signal.alarm(0)
        logger.error(f"部署过程中发生错误: {str(e)}")
        raise

def _deploy_with_basic_config(image_tag):
    """使用基本配置进行部署"""
    from prefect.client.orchestration import get_client
    
    logger.info(f"连接到Prefect API: {config.PREFECT_API_URL}")
    logger.info(f"工作池名称: {config.WORK_POOL_NAME}")
    
    # 检查Prefect API连接
    try:
        logger.info("正在检查Prefect API连接...")
        client = get_client()
        logger.info("成功连接到Prefect API")
        
        # 检查工作池是否存在
        logger.info(f"正在检查工作池 {config.WORK_POOL_NAME} 是否存在...")
        
    except Exception as e:
        logger.error(f"Prefect API连接失败: {str(e)}")
    
    logger.info("开始部署工作流...")
    logger.info(f"部署参数: name={config.DEPLOYMENT_NAME}, work_pool_name={config.WORK_POOL_NAME}, image={image_tag}")
    
    # 使用更基本的部署方式
    deployment_id = hello.deploy(
        name=config.DEPLOYMENT_NAME,
        work_pool_name=config.WORK_POOL_NAME,
        image=image_tag,
        job_variables={"env.PYTHONUNBUFFERED": "1"},
        tags=config.get_deployment_tags(),
        description=config.DEPLOYMENT_DESCRIPTION,
    )
    
    logger.info("部署命令已执行，等待结果...")
    return deployment_id

def _deploy_locally(image_tag):
    """在本地环境部署工作流"""
    # 创建临时日志目录以避免I/O错误
    temp_log_dir = tempfile.mkdtemp(prefix="prefect_logs_")
    
    # 配置Docker环境变量和选项
    docker_env = config.get_docker_job_variables()
    docker_env["env.PREFECT_DOCKER_VOLUME_MOUNTS"] = f"{temp_log_dir}:/tmp/prefect/logs"
    
    # 使用更稳健的部署配置
    hello.deploy(
        name=config.DEPLOYMENT_NAME,
        work_pool_name=config.WORK_POOL_NAME,
        image=image_tag,
        schedule=config.get_schedule_config(),
        description=config.DEPLOYMENT_DESCRIPTION,
        tags=config.get_deployment_tags(),
        job_variables=docker_env,
        concurrency_limit=config.CONCURRENCY_LIMIT
    )

if __name__ == "__main__":
    if config.DEPLOY_MODE:
        deploy_flow()
    else:
        hello()
