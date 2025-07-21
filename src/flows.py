"""
Prefect流定义模块
"""
import time
import logging
from prefect import flow, task

logger = logging.getLogger(__name__)


@task(name="greeting-task")
def generate_greeting(name: str = "World") -> str:
    """生成问候语的任务"""
    return f"Hello {name}! This run was scheduled via Interval!"


@task(name="sleep-task")
def sleep_task(duration: int = 20) -> None:
    """休眠任务"""
    logger.info(f"Sleeping for {duration} seconds...")
    time.sleep(duration)
    logger.info("Sleep completed!")


@flow(name="hello-flow", log_prints=True)
def hello_flow(name: str = "World") -> str:
    """主要的问候流"""
    greeting = generate_greeting(name)
    print(greeting)
    
    sleep_task()
    
    return greeting


@flow(name="health-check-flow")
def health_check_flow() -> dict:
    """健康检查流"""
    import datetime
    
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "message": "Flow is running successfully"
    }