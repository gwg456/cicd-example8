"""
Production-grade Prefect flows with monitoring and error handling
"""
import time
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from prefect import flow, task
from prefect.task_runners import ConcurrentTaskRunner

from src.monitoring import metrics, TaskLogger
from src.core import retry_with_backoff, measure_execution_time

logger = logging.getLogger(__name__)


@task(
    name="greeting-task",
    retries=2,
    retry_delay_seconds=5,
    tags=["production", "greeting"]
)
@measure_execution_time(metric_type="task", task_name="generate_greeting")
def generate_greeting(name: str = "World") -> str:
    """
    Generate a greeting message
    
    Args:
        name: Name to greet
    
    Returns:
        Greeting message
    """
    with TaskLogger("generate_greeting") as task_logger:
        task_logger.info("Generating greeting", name=name)
        
        # Validate input
        if not name or not isinstance(name, str):
            task_logger.warning("Invalid name provided, using default", provided_name=name)
            name = "World"
        
        # Sanitize input
        name = name.strip()[:100]  # Limit length for safety
        
        greeting = f"Hello {name}! This run was scheduled via Prefect."
        task_logger.info("Greeting generated", greeting=greeting)
        
        return greeting


@task(
    name="process-data-task",
    retries=3,
    retry_delay_seconds=10,
    tags=["production", "processing"]
)
@retry_with_backoff(max_attempts=3, max_delay=30)
@measure_execution_time(metric_type="task", task_name="process_data")
def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process input data with validation and transformation
    
    Args:
        data: Input data to process
    
    Returns:
        Processed data
    """
    with TaskLogger("process_data") as task_logger:
        task_logger.info("Processing data", data_size=len(str(data)))
        
        try:
            # Simulate data processing
            processed = {
                "original_keys": list(data.keys()),
                "processed_at": datetime.now().isoformat(),
                "item_count": len(data),
                "status": "processed"
            }
            
            # Add some business logic
            if "priority" in data and data["priority"] == "high":
                processed["fast_track"] = True
                task_logger.info("High priority data detected")
            
            task_logger.info("Data processed successfully", result=processed)
            return processed
            
        except Exception as e:
            task_logger.error("Data processing failed", error=str(e))
            metrics.record_error("ProcessingError", "process_data")
            raise


@task(
    name="sleep-task",
    timeout_seconds=60,
    tags=["production", "utility"]
)
def sleep_task(duration: int = 20) -> None:
    """
    Sleep task with monitoring
    
    Args:
        duration: Sleep duration in seconds
    """
    with TaskLogger("sleep_task") as task_logger:
        # Validate duration
        if duration < 0:
            task_logger.warning("Invalid duration, using default", provided_duration=duration)
            duration = 20
        elif duration > 300:
            task_logger.warning("Duration too long, capping at 300s", provided_duration=duration)
            duration = 300
        
        task_logger.info(f"Sleeping for {duration} seconds...")
        time.sleep(duration)
        task_logger.info("Sleep completed")


@flow(
    name="hello-flow",
    description="Production hello workflow with monitoring",
    task_runner=ConcurrentTaskRunner(),
    retries=1,
    retry_delay_seconds=30,
    log_prints=True,
    persist_result=True,
    result_storage_key="hello-flow-{flow_run.id}",
)
@measure_execution_time(metric_type="flow", flow_name="hello_flow")
def hello_flow(name: str = "World", include_processing: bool = True) -> Dict[str, Any]:
    """
    Main hello flow with comprehensive monitoring
    
    Args:
        name: Name to greet
        include_processing: Whether to include data processing
    
    Returns:
        Flow execution results
    """
    flow_logger = TaskLogger("hello_flow")
    flow_logger.info("Flow started", name=name, include_processing=include_processing)
    
    results = {
        "flow_id": str(flow.run_id) if hasattr(flow, 'run_id') else "local",
        "started_at": datetime.now().isoformat(),
        "parameters": {"name": name, "include_processing": include_processing}
    }
    
    try:
        # Generate greeting
        greeting = generate_greeting(name)
        results["greeting"] = greeting
        print(greeting)
        
        # Optional data processing
        if include_processing:
            sample_data = {
                "user": name,
                "timestamp": datetime.now().isoformat(),
                "priority": "high" if name.lower() in ["admin", "system"] else "normal"
            }
            processed_data = process_data(sample_data)
            results["processed_data"] = processed_data
        
        # Sleep task
        sleep_task(duration=10)
        
        results["status"] = "success"
        results["completed_at"] = datetime.now().isoformat()
        
        flow_logger.info("Flow completed successfully", results=results)
        metrics.record_flow("hello_flow", "success")
        
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        results["failed_at"] = datetime.now().isoformat()
        
        flow_logger.error("Flow failed", error=str(e))
        metrics.record_flow("hello_flow", "failure")
        raise
    
    return results


@flow(
    name="health-check-flow",
    description="System health check workflow",
    tags=["production", "monitoring", "health"],
    log_prints=True
)
def health_check_flow() -> Dict[str, Any]:
    """
    Health check flow for system monitoring
    
    Returns:
        Health check results
    """
    import psutil
    from src.config import get_settings
    
    settings = get_settings()
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": settings.environment.value,
        "checks": {}
    }
    
    try:
        # System resource checks
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data["checks"]["system"] = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "degraded"
        }
        
        # Prefect API check
        try:
            from prefect.client.orchestration import get_client
            import asyncio
            
            async def check_api():
                async with get_client() as client:
                    await client.api_healthcheck()
                    return True
            
            asyncio.run(check_api())
            health_data["checks"]["prefect_api"] = {"status": "healthy"}
        except Exception as e:
            health_data["checks"]["prefect_api"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # Overall status determination
        if any(check.get("status") == "unhealthy" for check in health_data["checks"].values()):
            health_data["status"] = "unhealthy"
        elif any(check.get("status") == "degraded" for check in health_data["checks"].values()):
            health_data["status"] = "degraded"
        
        logger.info(f"Health check completed: {health_data['status']}")
        metrics.record_flow("health_check_flow", "success")
        
    except Exception as e:
        health_data["status"] = "unhealthy"
        health_data["error"] = str(e)
        logger.error(f"Health check failed: {e}")
        metrics.record_flow("health_check_flow", "failure")
    
    return health_data


@flow(
    name="data-pipeline-flow",
    description="Production data processing pipeline",
    task_runner=ConcurrentTaskRunner(max_workers=4),
    tags=["production", "data", "pipeline"],
    persist_result=True
)
def data_pipeline_flow(
    batch_size: int = 100,
    parallel_workers: int = 4
) -> Dict[str, Any]:
    """
    Scalable data processing pipeline
    
    Args:
        batch_size: Size of data batches to process
        parallel_workers: Number of parallel workers
    
    Returns:
        Pipeline execution results
    """
    from concurrent.futures import ThreadPoolExecutor
    import random
    
    pipeline_logger = TaskLogger("data_pipeline_flow")
    pipeline_logger.info("Pipeline started", batch_size=batch_size, workers=parallel_workers)
    
    results = {
        "pipeline_id": str(flow.run_id) if hasattr(flow, 'run_id') else "local",
        "started_at": datetime.now().isoformat(),
        "batch_size": batch_size,
        "parallel_workers": parallel_workers,
        "batches_processed": 0,
        "items_processed": 0
    }
    
    try:
        # Generate sample data batches
        batches = []
        for i in range(5):  # Process 5 batches
            batch = {
                "batch_id": i,
                "items": [{"id": j, "value": random.random()} for j in range(batch_size)],
                "priority": random.choice(["low", "normal", "high"])
            }
            batches.append(batch)
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
            processed_batches = list(executor.map(process_data, batches))
        
        results["batches_processed"] = len(processed_batches)
        results["items_processed"] = len(batches) * batch_size
        results["status"] = "success"
        results["completed_at"] = datetime.now().isoformat()
        
        pipeline_logger.info("Pipeline completed", results=results)
        metrics.record_flow("data_pipeline_flow", "success")
        
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        pipeline_logger.error("Pipeline failed", error=str(e))
        metrics.record_flow("data_pipeline_flow", "failure")
        raise
    
    return results