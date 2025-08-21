"""
健康检查模块

提供应用程序健康状态检查功能。
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from prefect.client.orchestration import get_client

from config import config
from src.logging_config import get_logger

logger = get_logger(__name__)


class HealthCheck:
    """健康检查基类"""
    
    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
    
    async def check(self) -> Dict[str, Any]:
        """执行健康检查"""
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(self._check_impl(), timeout=self.timeout)
            duration = time.time() - start_time
            
            return {
                "name": self.name,
                "status": "healthy" if result.get("healthy", False) else "unhealthy",
                "duration_ms": round(duration * 1000, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": result,
            }
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return {
                "name": self.name,
                "status": "timeout",
                "duration_ms": round(duration * 1000, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"Health check timed out after {self.timeout}s",
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "name": self.name,
                "status": "error",
                "duration_ms": round(duration * 1000, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            }
    
    async def _check_impl(self) -> Dict[str, Any]:
        """子类需要实现的具体检查逻辑"""
        raise NotImplementedError


class PrefectHealthCheck(HealthCheck):
    """Prefect API健康检查"""
    
    def __init__(self, timeout: float = 10.0):
        super().__init__("prefect_api", timeout)
    
    async def _check_impl(self) -> Dict[str, Any]:
        """检查Prefect API连接"""
        try:
            async with get_client() as client:
                health_response = await client.api_healthcheck()
                
                return {
                    "healthy": True,
                    "api_url": config.prefect_api_url,
                    "response": health_response,
                }
        except Exception as e:
            logger.error("Prefect API health check failed", error=str(e))
            return {
                "healthy": False,
                "api_url": config.prefect_api_url,
                "error": str(e),
            }


class DatabaseHealthCheck(HealthCheck):
    """数据库健康检查（如果使用）"""
    
    def __init__(self, timeout: float = 5.0):
        super().__init__("database", timeout)
    
    async def _check_impl(self) -> Dict[str, Any]:
        """检查数据库连接"""
        # 这里可以添加数据库连接检查
        # 目前项目没有直接的数据库连接，所以返回健康状态
        return {
            "healthy": True,
            "message": "No direct database connection required",
        }


class DiskSpaceHealthCheck(HealthCheck):
    """磁盘空间健康检查"""
    
    def __init__(self, threshold_percent: float = 90.0, timeout: float = 2.0):
        super().__init__("disk_space", timeout)
        self.threshold_percent = threshold_percent
    
    async def _check_impl(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        import shutil
        
        try:
            total, used, free = shutil.disk_usage("/")
            used_percent = (used / total) * 100
            
            return {
                "healthy": used_percent < self.threshold_percent,
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "used_percent": round(used_percent, 2),
                "threshold_percent": self.threshold_percent,
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }


class MemoryHealthCheck(HealthCheck):
    """内存使用健康检查"""
    
    def __init__(self, threshold_percent: float = 90.0, timeout: float = 2.0):
        super().__init__("memory", timeout)
        self.threshold_percent = threshold_percent
    
    async def _check_impl(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            return {
                "healthy": memory.percent < self.threshold_percent,
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_percent": memory.percent,
                "threshold_percent": self.threshold_percent,
            }
        except ImportError:
            return {
                "healthy": True,
                "message": "psutil not available, skipping memory check",
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }


class ConfigurationHealthCheck(HealthCheck):
    """配置健康检查"""
    
    def __init__(self, timeout: float = 1.0):
        super().__init__("configuration", timeout)
    
    async def _check_impl(self) -> Dict[str, Any]:
        """检查配置完整性"""
        missing_configs = config.validate_required_settings()
        
        return {
            "healthy": len(missing_configs) == 0,
            "missing_configs": missing_configs,
            "environment": config.environment,
            "deploy_mode": config.deploy_mode,
            "log_level": config.log_level,
        }


class HealthChecker:
    """健康检查管理器"""
    
    def __init__(self):
        self.checks: List[HealthCheck] = [
            ConfigurationHealthCheck(),
            PrefectHealthCheck(),
            DiskSpaceHealthCheck(),
            MemoryHealthCheck(),
            DatabaseHealthCheck(),
        ]
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        start_time = time.time()
        
        # 并行执行所有检查
        results = await asyncio.gather(
            *[check.check() for check in self.checks],
            return_exceptions=True
        )
        
        # 处理结果
        check_results = []
        overall_healthy = True
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                check_result = {
                    "name": self.checks[i].name,
                    "status": "error",
                    "error": str(result),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                overall_healthy = False
            else:
                check_result = result
                if result.get("status") != "healthy":
                    overall_healthy = False
            
            check_results.append(check_result)
        
        total_duration = time.time() - start_time
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": round(total_duration * 1000, 2),
            "checks": check_results,
            "summary": {
                "total_checks": len(check_results),
                "healthy_checks": len([c for c in check_results if c.get("status") == "healthy"]),
                "unhealthy_checks": len([c for c in check_results if c.get("status") != "healthy"]),
            },
            "version": "1.0.0",
            "environment": config.environment,
        }
    
    async def run_check(self, check_name: str) -> Optional[Dict[str, Any]]:
        """运行特定的健康检查"""
        for check in self.checks:
            if check.name == check_name:
                return await check.check()
        return None
    
    def add_check(self, check: HealthCheck) -> None:
        """添加自定义健康检查"""
        self.checks.append(check)


# 全局健康检查器实例
health_checker = HealthChecker()


async def get_health_status() -> Dict[str, Any]:
    """获取应用健康状态"""
    return await health_checker.run_all_checks()


async def get_readiness_status() -> Dict[str, Any]:
    """获取应用就绪状态（主要检查关键依赖）"""
    # 只检查关键的健康检查项
    critical_checks = ["configuration", "prefect_api"]
    
    results = []
    overall_ready = True
    
    for check_name in critical_checks:
        result = await health_checker.run_check(check_name)
        if result:
            results.append(result)
            if result.get("status") != "healthy":
                overall_ready = False
    
    return {
        "status": "ready" if overall_ready else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": results,
    }


async def get_liveness_status() -> Dict[str, Any]:
    """获取应用存活状态（简单检查）"""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": time.time() - getattr(get_liveness_status, "_start_time", time.time()),
    }


# 记录启动时间
get_liveness_status._start_time = time.time()
