import time
import os
import datetime
import logging
import tempfile
from prefect import flow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

IMAGE_REPO = os.environ.get("IMAGE_REPO", "ghcr.io/samples28/cicd-example")
WORK_POOL_NAME = os.environ.get("WORK_POOL_NAME", "my-docker-pool2")

@flow(log_prints=True)
def hello():
    print("Hello word!20259 - This run was scheduled via Interval!")
    time.sleep(20)

def deploy_flow():
    try:
        # 使用环境变量中的镜像标签（如果存在），否则生成一个新的标签
        image_tag = ""
        if os.environ.get("IMAGE_TAG"):
            image_tag = f"{IMAGE_REPO}:{os.environ.get('IMAGE_TAG')}"
            logger.info(f"使用GitHub Actions提供的镜像标签: {image_tag}")
        else:
            current_time = datetime.datetime.now()
            version_tag = f"v{current_time.strftime('%Y%m%d%H%M')}"
            image_tag = f"{IMAGE_REPO}:{version_tag}"
            logger.info(f"本地生成镜像标签: {image_tag}")
        
        print(f"正在部署镜像: {image_tag}")
        
        # 创建临时日志目录以避免I/O错误
        temp_log_dir = tempfile.mkdtemp(prefix="prefect_logs_")
        
        # 配置Docker环境变量和选项
        docker_env = {
            "env.LOG_LEVEL": "INFO",
            "env.ENVIRONMENT": "production",
            "env.PYTHONUNBUFFERED": "1",
            "env.DOCKER_CLIENT_TIMEOUT": "300",
            "env.COMPOSE_HTTP_TIMEOUT": "300",
            "env.PREFECT_LOGGING_LEVEL": "INFO",
            "env.PREFECT_API_RESPONSE_TIMEOUT": "300",
            "env.PREFECT_API_REQUEST_TIMEOUT": "300",
            "env.PREFECT_DOCKER_HOST_NETWORK": "true",
            "env.PREFECT_DOCKER_VOLUME_MOUNTS": f"{temp_log_dir}:/tmp/prefect/logs",
            "env.PREFECT_DOCKER_NETWORK": "host"
        }
        
        # 使用更稳健的部署配置
        hello.deploy(
            name="prod-deployment",
            work_pool_name=WORK_POOL_NAME,
            image=image_tag,
            schedule={"interval": 3600},
            description="生产环境部署的hello流",
            tags=["production", "automated"],
            job_variables=docker_env,
            concurrency_limit=2
        )
        
        print(f"部署已完成，版本: {image_tag}")
        
        if not os.environ.get("IMAGE_TAG"):
            print("注意: 部署前，请确保您的Docker镜像已构建并推送:")
            print(f"  docker build -t {image_tag} .")
            print(f"  docker push {image_tag}")
        
    except Exception as e:
        logger.error(f"部署过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    deploy_flow()
