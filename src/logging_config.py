"""
结构化日志配置模块

提供统一的日志配置和结构化日志记录功能。
"""
import logging
import sys
from typing import Any, Dict, Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler

from config import config


def configure_logging() -> None:
    """配置结构化日志"""
    
    # 配置标准库logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.log_level.upper()),
        handlers=[
            RichHandler(
                console=Console(stderr=False),
                show_time=True,
                show_path=True,
                markup=True,
                rich_tracebacks=True,
            )
        ],
    )
    
    # 配置structlog
    structlog.configure(
        processors=[
            # 添加时间戳
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            # 添加调用信息
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            # 格式化异常
            structlog.processors.format_exc_info,
            # 添加环境信息
            add_environment_context,
            # JSON格式化（生产环境）或彩色输出（开发环境）
            structlog.processors.JSONRenderer() if config.is_production
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_environment_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """添加环境上下文信息"""
    event_dict.update({
        "environment": config.environment,
        "service": "prefect-cicd",
        "version": "1.0.0",
        "container": config.is_container_env,
    })
    return event_dict


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)


class LoggerMixin:
    """日志记录器混入类"""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """获取当前类的日志记录器"""
        return get_logger(self.__class__.__name__)


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, logger: structlog.stdlib.BoundLogger):
        self.logger = logger
        self._start_time: Optional[float] = None
    
    def start(self, operation: str, **kwargs) -> None:
        """开始性能监控"""
        import time
        self._start_time = time.time()
        self.logger.info("Performance monitoring started", 
                        operation=operation, **kwargs)
    
    def end(self, operation: str, **kwargs) -> float:
        """结束性能监控并记录耗时"""
        import time
        if self._start_time is None:
            self.logger.warning("Performance monitoring not started")
            return 0.0
        
        duration = time.time() - self._start_time
        self.logger.info("Performance monitoring completed",
                        operation=operation,
                        duration_seconds=duration,
                        **kwargs)
        self._start_time = None
        return duration


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, logger: structlog.stdlib.BoundLogger):
        self.logger = logger.bind(log_type="audit")
    
    def log_deployment(self, flow_name: str, deployment_id: str, status: str, **kwargs) -> None:
        """记录部署事件"""
        self.logger.info("Deployment event",
                        flow_name=flow_name,
                        deployment_id=deployment_id,
                        status=status,
                        **kwargs)
    
    def log_flow_execution(self, flow_name: str, run_id: str, status: str, **kwargs) -> None:
        """记录流程执行事件"""
        self.logger.info("Flow execution event",
                        flow_name=flow_name,
                        run_id=run_id,
                        status=status,
                        **kwargs)
    
    def log_configuration_change(self, setting: str, old_value: Any, new_value: Any, **kwargs) -> None:
        """记录配置变更事件"""
        self.logger.info("Configuration change",
                        setting=setting,
                        old_value=str(old_value),
                        new_value=str(new_value),
                        **kwargs)


class SecurityLogger:
    """安全日志记录器"""
    
    def __init__(self, logger: structlog.stdlib.BoundLogger):
        self.logger = logger.bind(log_type="security")
    
    def log_authentication_attempt(self, user: str, success: bool, **kwargs) -> None:
        """记录认证尝试"""
        self.logger.info("Authentication attempt",
                        user=user,
                        success=success,
                        **kwargs)
    
    def log_authorization_failure(self, user: str, resource: str, action: str, **kwargs) -> None:
        """记录授权失败"""
        self.logger.warning("Authorization failure",
                           user=user,
                           resource=resource,
                           action=action,
                           **kwargs)
    
    def log_suspicious_activity(self, activity: str, details: Dict[str, Any], **kwargs) -> None:
        """记录可疑活动"""
        self.logger.warning("Suspicious activity detected",
                           activity=activity,
                           details=details,
                           **kwargs)


# 全局日志记录器实例
def setup_global_loggers() -> Dict[str, Any]:
    """设置全局日志记录器"""
    configure_logging()
    
    main_logger = get_logger("main")
    performance_logger = PerformanceLogger(get_logger("performance"))
    audit_logger = AuditLogger(get_logger("audit"))
    security_logger = SecurityLogger(get_logger("security"))
    
    return {
        "main": main_logger,
        "performance": performance_logger,
        "audit": audit_logger,
        "security": security_logger,
    }


# 装饰器
def log_execution_time(logger: Optional[structlog.stdlib.BoundLogger] = None):
    """装饰器：记录函数执行时间"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            import functools
            
            _logger = logger or get_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                _logger.info("Function executed successfully",
                           function=func.__name__,
                           duration_seconds=duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                _logger.error("Function execution failed",
                            function=func.__name__,
                            duration_seconds=duration,
                            error=str(e))
                raise
        
        return functools.wraps(func)(wrapper)
    return decorator


def log_function_call(logger: Optional[structlog.stdlib.BoundLogger] = None):
    """装饰器：记录函数调用"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import functools
            
            _logger = logger or get_logger(func.__module__)
            _logger.debug("Function called",
                         function=func.__name__,
                         args=len(args),
                         kwargs=list(kwargs.keys()))
            
            return func(*args, **kwargs)
        
        return functools.wraps(func)(wrapper)
    return decorator
