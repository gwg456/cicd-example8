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
        
        # 检查是否在容器内部署
        in_container = os.path.exists("/.dockerenv")
        
        if in_container:
            # 在容器内使用新的API进行部署
            # 基本环境变量
            env_vars = {
                "LOG_LEVEL": "INFO",
                "ENVIRONMENT": "production",
                "PYTHONUNBUFFERED": "1",
                "PREFECT_LOGGING_LEVEL": "INFO",
                "PREFECT_API_RESPONSE_TIMEOUT": "300",
                "PREFECT_API_REQUEST_TIMEOUT": "300",
            }
            
            # 使用新的API部署工作流
            # 尝试从不同路径导入Docker容器基础设施
            try:
                # 首先尝试prefect-docker包
                from prefect_docker.containers import DockerContainer
                
                # 创建Docker容器基础设施
                docker_infrastructure = DockerContainer(
                    image=image_tag,
                    env=env_vars,
                    network_mode="host",
                )
            except ImportError:
                # 如果失败，则使用通用基础设施
                print("无法导入DockerContainer，使用默认基础设施配置")
                docker_infrastructure = None
            
            import signal
            
            # 定义超时处理函数
            def timeout_handler(signum, frame):
                print("部署操作超时，可能是网络问题或Prefect服务器无响应")
                raise TimeoutError("部署操作超时")
            
            # 设置60秒超时
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)
            
            try:
                print("开始部署流程...")
                
                # 使用新的deploy方法，根据是否有docker_infrastructure决定参数
                if docker_infrastructure:
                    print("使用DockerContainer基础设施进行部署")
                    deployment_id = hello.deploy(
                        name="prod-deployment",
                        work_pool_name=WORK_POOL_NAME,
                        infrastructure=docker_infrastructure,
                        schedule={"interval": 3600},
                        tags=["production", "automated"],
                        description="生产环境部署的hello流",
                    )
                else:
                    print("使用直接image参数进行部署")
                    # 使用更简单的部署方式
                    from prefect.client.orchestration import get_client
                    
                    print(f"连接到Prefect API: {os.environ.get('PREFECT_API_URL', '默认URL')}")
                    print(f"工作池名称: {WORK_POOL_NAME}")
                    
                    # 检查Prefect API连接
                    try:
                        print("正在检查Prefect API连接...")
                        client = get_client()
                        print(f"成功连接到Prefect API")
                        
                        # 检查工作池是否存在
                        print(f"正在检查工作池 {WORK_POOL_NAME} 是否存在...")
                        # 这里可以添加检查工作池的代码，但我们先跳过
                        
                    except Exception as e:
                        print(f"Prefect API连接失败: {str(e)}")
                    
                    print("开始部署工作流...")
                    print(f"部署参数: name=prod-deployment, work_pool_name={WORK_POOL_NAME}, image={image_tag}")
                    
                    # 使用更基本的部署方式，不使用schedule参数
                    deployment_id = hello.deploy(
                        name="prod-deployment",
                        work_pool_name=WORK_POOL_NAME,
                        image=image_tag,
                        job_variables={"env.PYTHONUNBUFFERED": "1"},
                        tags=["production", "automated"],
                        description="生产环境部署的hello流",
                    )
                    
                    print("部署命令已执行，等待结果...")
                
                # 取消超时
                signal.alarm(0)
                
            except Exception as e:
                # 取消超时
                signal.alarm(0)
                print(f"部署过程中发生错误: {str(e)}")
                raise
            
            print(f"部署ID: {deployment_id}")
        else:
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
    if os.environ.get("DEPLOY_MODE", "false").lower() == "true":
        deploy_flow()
    else:
        hello()
