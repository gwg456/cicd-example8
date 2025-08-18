"""
Health check endpoints and monitoring
"""
import asyncio
import os
import psutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from src.config import get_settings
from src.monitoring.metrics import metrics


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of a component"""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    checked_at: datetime = datetime.now()


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: HealthStatus
    timestamp: datetime
    version: str
    environment: str
    components: List[ComponentHealth]
    metrics: Optional[Dict[str, Any]] = None


class HealthCheck:
    """Health check implementation"""
    
    def __init__(self):
        self.settings = get_settings()
        self.checks = []
        
        # Register default checks
        self.register_check("system", self._check_system)
        self.register_check("prefect_api", self._check_prefect_api)
        self.register_check("database", self._check_database)
        self.register_check("redis", self._check_redis)
    
    def register_check(self, name: str, check_func):
        """Register a health check function"""
        self.checks.append((name, check_func))
    
    async def _check_system(self) -> ComponentHealth:
        """Check system resources"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            messages = []
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High CPU usage: {cpu_percent}%")
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                messages.append(f"Elevated CPU usage: {cpu_percent}%")
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High memory usage: {memory.percent}%")
            elif memory.percent > 70:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                messages.append(f"Elevated memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High disk usage: {disk.percent}%")
            elif disk.percent > 80:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                messages.append(f"Elevated disk usage: {disk.percent}%")
            
            return ComponentHealth(
                name="system",
                status=status,
                message="; ".join(messages) if messages else "System resources OK",
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3),
                    "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
                }
            )
        except Exception as e:
            return ComponentHealth(
                name="system",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check system resources: {str(e)}"
            )
    
    async def _check_prefect_api(self) -> ComponentHealth:
        """Check Prefect API connectivity"""
        try:
            from prefect.client.orchestration import get_client
            
            async with get_client() as client:
                # Attempt health check with timeout
                await asyncio.wait_for(
                    client.api_healthcheck(),
                    timeout=5.0
                )
            
            return ComponentHealth(
                name="prefect_api",
                status=HealthStatus.HEALTHY,
                message="Prefect API is reachable",
                details={
                    "api_url": str(self.settings.prefect_api_url)
                }
            )
        except asyncio.TimeoutError:
            return ComponentHealth(
                name="prefect_api",
                status=HealthStatus.UNHEALTHY,
                message="Prefect API connection timeout"
            )
        except Exception as e:
            return ComponentHealth(
                name="prefect_api",
                status=HealthStatus.UNHEALTHY,
                message=f"Prefect API check failed: {str(e)}"
            )
    
    async def _check_database(self) -> ComponentHealth:
        """Check database connectivity"""
        # This is a placeholder - implement based on your database setup
        try:
            # Example for SQLAlchemy
            # from src.database import engine
            # async with engine.connect() as conn:
            #     await conn.execute("SELECT 1")
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection OK"
            )
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {str(e)}"
            )
    
    async def _check_redis(self) -> ComponentHealth:
        """Check Redis connectivity"""
        # This is a placeholder - implement based on your Redis setup
        try:
            # Example for Redis
            # import redis.asyncio as redis
            # r = redis.Redis(host='localhost', port=6379)
            # await r.ping()
            
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis connection OK"
            )
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.DEGRADED,
                message=f"Redis not available: {str(e)}"
            )
    
    async def check_health(self) -> HealthCheckResponse:
        """Perform all health checks"""
        components = []
        
        # Run all checks in parallel
        check_tasks = [check_func() for name, check_func in self.checks]
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                components.append(ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(result)}"
                ))
            else:
                components.append(result)
        
        # Determine overall status
        statuses = [c.status for c in components]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        # Get application version
        try:
            with open("VERSION", "r") as f:
                version = f.read().strip()
        except:
            version = "unknown"
        
        # Collect metrics
        health_metrics = {
            "uptime_seconds": (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds(),
            "process_uptime_seconds": (datetime.now() - datetime.fromtimestamp(psutil.Process().create_time())).total_seconds(),
        }
        
        # Update metrics
        metrics.update_memory_usage()
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version=version,
            environment=self.settings.environment.value,
            components=components,
            metrics=health_metrics
        )
    
    async def check_liveness(self) -> bool:
        """Simple liveness check"""
        # Basic check that the application is running
        return True
    
    async def check_readiness(self) -> bool:
        """Readiness check for load balancer"""
        # Check if critical components are ready
        health_response = await self.check_health()
        return health_response.status != HealthStatus.UNHEALTHY


# Create health check router for FastAPI
health_check_router = APIRouter(prefix="/health", tags=["health"])
health_checker = HealthCheck()


@health_check_router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    return await health_checker.check_health()


@health_check_router.get("/live")
async def liveness_check(response: Response):
    """Kubernetes liveness probe endpoint"""
    is_alive = await health_checker.check_liveness()
    if not is_alive:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy"}
    return {"status": "healthy"}


@health_check_router.get("/ready")
async def readiness_check(response: Response):
    """Kubernetes readiness probe endpoint"""
    is_ready = await health_checker.check_readiness()
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready"}
    return {"status": "ready"}


@health_check_router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    metrics_data = metrics.get_metrics()
    return Response(
        content=metrics_data,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )