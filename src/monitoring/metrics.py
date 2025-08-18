"""
Metrics collection and monitoring with Prometheus
"""
import time
import functools
import logging
from typing import Any, Callable, Optional, Dict
from contextlib import contextmanager
from datetime import datetime

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    start_http_server,
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Centralized metrics collection for the application"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        
        # Request metrics
        self.request_count = Counter(
            'app_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'app_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Task metrics
        self.task_count = Counter(
            'prefect_tasks_total',
            'Total number of Prefect tasks',
            ['task_name', 'status'],
            registry=self.registry
        )
        
        self.task_duration = Histogram(
            'prefect_task_duration_seconds',
            'Task execution duration in seconds',
            ['task_name'],
            registry=self.registry
        )
        
        # Flow metrics
        self.flow_count = Counter(
            'prefect_flows_total',
            'Total number of Prefect flows',
            ['flow_name', 'status'],
            registry=self.registry
        )
        
        self.flow_duration = Histogram(
            'prefect_flow_duration_seconds',
            'Flow execution duration in seconds',
            ['flow_name'],
            registry=self.registry
        )
        
        # Deployment metrics
        self.deployment_count = Counter(
            'deployments_total',
            'Total number of deployments',
            ['deployment_name', 'status'],
            registry=self.registry
        )
        
        self.deployment_duration = Histogram(
            'deployment_duration_seconds',
            'Deployment duration in seconds',
            ['deployment_name'],
            registry=self.registry
        )
        
        # API call metrics
        self.api_call_count = Counter(
            'external_api_calls_total',
            'Total number of external API calls',
            ['service', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.api_call_duration = Histogram(
            'external_api_call_duration_seconds',
            'External API call duration in seconds',
            ['service', 'endpoint'],
            registry=self.registry
        )
        
        # Error metrics
        self.error_count = Counter(
            'app_errors_total',
            'Total number of errors',
            ['error_type', 'component'],
            registry=self.registry
        )
        
        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            'circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=open, 2=half-open)',
            ['breaker_name'],
            registry=self.registry
        )
        
        self.circuit_breaker_trips = Counter(
            'circuit_breaker_trips_total',
            'Total number of circuit breaker trips',
            ['breaker_name'],
            registry=self.registry
        )
        
        # Retry metrics
        self.retry_count = Counter(
            'retries_total',
            'Total number of retries',
            ['operation', 'status'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total number of cache hits',
            ['cache_name'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total number of cache misses',
            ['cache_name'],
            registry=self.registry
        )
        
        # System metrics
        self.active_connections = Gauge(
            'active_connections',
            'Number of active connections',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],
            registry=self.registry
        )
        
        # Application info
        self.app_info = Info(
            'app_info',
            'Application information',
            registry=self.registry
        )
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        self.request_count.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_task(self, task_name: str, status: str, duration: Optional[float] = None):
        """Record Prefect task metrics"""
        self.task_count.labels(task_name=task_name, status=status).inc()
        if duration is not None:
            self.task_duration.labels(task_name=task_name).observe(duration)
    
    def record_flow(self, flow_name: str, status: str, duration: Optional[float] = None):
        """Record Prefect flow metrics"""
        self.flow_count.labels(flow_name=flow_name, status=status).inc()
        if duration is not None:
            self.flow_duration.labels(flow_name=flow_name).observe(duration)
    
    def record_deployment(self, deployment_name: str, success: bool, duration: float):
        """Record deployment metrics"""
        status = "success" if success else "failure"
        self.deployment_count.labels(deployment_name=deployment_name, status=status).inc()
        self.deployment_duration.labels(deployment_name=deployment_name).observe(duration)
    
    def record_api_call(self, service: str, endpoint: str = "", success: bool = True, duration: Optional[float] = None):
        """Record external API call metrics"""
        status = "success" if success else "failure"
        self.api_call_count.labels(service=service, endpoint=endpoint, status=status).inc()
        if duration is not None:
            self.api_call_duration.labels(service=service, endpoint=endpoint).observe(duration)
    
    def record_error(self, error_type: str, component: str):
        """Record error metrics"""
        self.error_count.labels(error_type=error_type, component=component).inc()
    
    def update_circuit_breaker(self, breaker_name: str, state: int, trips: Optional[int] = None):
        """Update circuit breaker metrics"""
        self.circuit_breaker_state.labels(breaker_name=breaker_name).set(state)
        if trips is not None:
            for _ in range(trips):
                self.circuit_breaker_trips.labels(breaker_name=breaker_name).inc()
    
    def record_retry(self, operation: str, success: bool):
        """Record retry metrics"""
        status = "success" if success else "failure"
        self.retry_count.labels(operation=operation, status=status).inc()
    
    def record_cache_hit(self, cache_name: str):
        """Record cache hit"""
        self.cache_hits.labels(cache_name=cache_name).inc()
    
    def record_cache_miss(self, cache_name: str):
        """Record cache miss"""
        self.cache_misses.labels(cache_name=cache_name).inc()
    
    def update_active_connections(self, count: int):
        """Update active connections gauge"""
        self.active_connections.set(count)
    
    def update_memory_usage(self):
        """Update memory usage metrics"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        self.memory_usage.labels(type='rss').set(memory_info.rss)
        self.memory_usage.labels(type='vms').set(memory_info.vms)
    
    def set_app_info(self, **info):
        """Set application information"""
        self.app_info.info(info)
    
    @contextmanager
    def measure_time(self, metric_type: str, **labels):
        """Context manager to measure execution time"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            if metric_type == "request":
                self.request_duration.labels(**labels).observe(duration)
            elif metric_type == "task":
                self.task_duration.labels(**labels).observe(duration)
            elif metric_type == "flow":
                self.flow_duration.labels(**labels).observe(duration)
            elif metric_type == "api_call":
                self.api_call_duration.labels(**labels).observe(duration)
            elif metric_type == "deployment":
                self.deployment_duration.labels(**labels).observe(duration)
    
    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format"""
        return generate_latest(self.registry)
    
    def start_metrics_server(self, port: int = 8000):
        """Start Prometheus metrics server"""
        try:
            start_http_server(port, registry=self.registry)
            logger.info(f"Metrics server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")


# Global metrics instance
metrics = MetricsCollector()


def measure_execution_time(metric_type: str = "task", **metric_labels):
    """
    Decorator to measure function execution time
    
    Args:
        metric_type: Type of metric to record
        **metric_labels: Labels for the metric
    
    Example:
        @measure_execution_time(metric_type="task", task_name="process_data")
        def process_data():
            # Function logic
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            error_occurred = False
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_occurred = True
                metrics.record_error(
                    error_type=type(e).__name__,
                    component=func.__name__
                )
                raise
            finally:
                duration = time.time() - start_time
                status = "failure" if error_occurred else "success"
                
                # Record metrics based on type
                if metric_type == "task":
                    task_name = metric_labels.get("task_name", func.__name__)
                    metrics.record_task(task_name, status, duration)
                elif metric_type == "flow":
                    flow_name = metric_labels.get("flow_name", func.__name__)
                    metrics.record_flow(flow_name, status, duration)
                elif metric_type == "api_call":
                    service = metric_labels.get("service", "unknown")
                    endpoint = metric_labels.get("endpoint", func.__name__)
                    metrics.record_api_call(service, endpoint, not error_occurred, duration)
        
        return wrapper
    return decorator


def track_circuit_breaker(breaker):
    """
    Track circuit breaker metrics
    
    Args:
        breaker: CircuitBreaker instance to track
    """
    from src.core.circuit_breaker import CircuitState
    
    # Map circuit states to numeric values
    state_map = {
        CircuitState.CLOSED: 0,
        CircuitState.OPEN: 1,
        CircuitState.HALF_OPEN: 2,
    }
    
    # Get current state
    state_value = state_map.get(breaker.state, -1)
    
    # Update metrics
    metrics.update_circuit_breaker(
        breaker_name=breaker.name,
        state=state_value
    )


class MetricsMiddleware:
    """Middleware for automatic metrics collection"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        path = scope["path"]
        method = scope["method"]
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                status = message.get("status", 200)
                metrics.record_request(method, path, status, duration)
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_request(method, path, 500, duration)
            metrics.record_error(type(e).__name__, "http_middleware")
            raise