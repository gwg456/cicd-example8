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


@task(name="process-pdf-task")
def process_pdf(file_path: str = "example.pdf") -> str:
    """模拟处理PDF文件的任务"""
    logger.info(f"开始处理PDF文件: {file_path}")
    # 在实际应用中，这里会调用 tools/extract_pdf_text.py 的逻辑
    processing_time = round(time.time() % 5 + 1)  # 模拟1-6秒的处理时间
    time.sleep(processing_time)
    result = f"文件 '{file_path}' 处理完成，耗时 {processing_time} 秒。"
    logger.info(result)
    return result


@flow(name="process-pdf-flow", log_prints=True)
def process_pdf_flow():
    """处理PDF文件的工作流"""
    print("启动PDF处理流程...")
    process_pdf("通信网络安全防护公益培训.pdf")
