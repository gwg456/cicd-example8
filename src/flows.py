"""
Prefect流定义模块

定义项目中使用的所有Prefect流和任务。
包含主要的业务逻辑流和健康检查流。
"""
import time
import logging
from typing import Dict, Any
from datetime import datetime
from prefect import flow, task

logger = logging.getLogger(__name__)


@task(name="greeting-task")
def generate_greeting(name: str = "World") -> str:
    """
    生成问候语的任务
    
    Args:
        name: 要问候的名称，默认为"World"
        
    Returns:
        str: 格式化的问候语字符串
        
    Example:
        >>> generate_greeting("Alice")
        "Hello Alice! This run was scheduled via Interval!"
    """
    return f"Hello {name}! This run was scheduled via Interval!"


@task(name="sleep-task")
def sleep_task(duration: int = 20) -> None:
    """
    休眠任务，用于模拟长时间运行的任务
    
    Args:
        duration: 休眠时间（秒），默认为20秒
        
    Note:
        此任务主要用于演示目的，在实际应用中应替换为真实的业务逻辑
    """
    logger.info(f"Sleeping for {duration} seconds...")
    time.sleep(duration)
    logger.info("Sleep completed!")


@flow(name="hello-flow", log_prints=True)
def hello_flow(name: str = "World") -> str:
    """
    主要的问候流
    
    这是项目的核心流程，演示了如何组合多个任务来完成一个完整的工作流。
    流程包括生成问候语和执行休眠任务。
    
    Args:
        name: 要问候的名称，默认为"World"
        
    Returns:
        str: 生成的问候语
        
    Raises:
        Exception: 当任务执行失败时抛出异常
        
    Example:
        >>> hello_flow("Production")
        "Hello Production! This run was scheduled via Interval!"
    """
    greeting = generate_greeting(name)
    print(greeting)
    
    sleep_task()
    
    return greeting


@flow(name="health-check-flow")
def health_check_flow() -> Dict[str, Any]:
    """
    健康检查流
    
    用于监控系统状态和流的健康状况。定期执行此流可以确保
    Prefect环境正常运行，并提供系统状态的实时反馈。
    
    Returns:
        Dict[str, Any]: 包含健康状态信息的字典，包括：
            - status: 健康状态（"healthy"或"unhealthy"）
            - timestamp: 检查时间的ISO格式字符串
            - message: 状态描述信息
            
    Example:
        >>> health_check_flow()
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00.123456",
            "message": "Flow is running successfully"
        }
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Flow is running successfully"
    }