"""
Structured logging configuration with correlation IDs
"""
import logging
import sys
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import uuid

import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level
from structlog.stdlib import BoundLogger, LoggerFactory

# Context variable for request/correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def add_correlation_id(logger, method_name, event_dict):
    """Add correlation ID to log entries"""
    cid = correlation_id.get()
    if cid:
        event_dict['correlation_id'] = cid
    return event_dict


def add_app_context(logger, method_name, event_dict):
    """Add application context to log entries"""
    from src.config import get_settings
    settings = get_settings()
    
    event_dict['environment'] = settings.environment.value
    event_dict['app_name'] = settings.app_name
    
    if settings.is_container_env:
        event_dict['container'] = True
    
    return event_dict


def format_exception(logger, method_name, event_dict):
    """Format exception information"""
    if 'exc_info' in event_dict:
        exc_info = event_dict.pop('exc_info')
        if exc_info:
            event_dict['exception'] = {
                'type': exc_info[0].__name__ if exc_info[0] else 'Unknown',
                'message': str(exc_info[1]) if exc_info[1] else '',
                'traceback': traceback.format_exception(*exc_info)
            }
    return event_dict


def censor_sensitive_data(logger, method_name, event_dict):
    """Remove sensitive data from logs"""
    sensitive_keys = [
        'password', 'token', 'api_key', 'secret', 'authorization',
        'credit_card', 'ssn', 'jwt', 'bearer'
    ]
    
    def censor_dict(d):
        for key in list(d.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                d[key] = '***REDACTED***'
            elif isinstance(d[key], dict):
                censor_dict(d[key])
            elif isinstance(d[key], list):
                for item in d[key]:
                    if isinstance(item, dict):
                        censor_dict(item)
    
    censor_dict(event_dict)
    return event_dict


class CustomJSONRenderer(JSONRenderer):
    """Custom JSON renderer with pretty printing option"""
    
    def __init__(self, pretty: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.pretty = pretty
    
    def __call__(self, logger, method_name, event_dict):
        if self.pretty:
            return json.dumps(event_dict, indent=2, default=str)
        return super().__call__(logger, method_name, event_dict)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    pretty: bool = False,
    correlation_id_header: str = "X-Correlation-ID"
) -> None:
    """
    Set up structured logging for the application
    
    Args:
        log_level: Logging level
        log_format: Log format ('json' or 'console')
        pretty: Pretty print JSON logs
        correlation_id_header: Header name for correlation ID
    """
    # Configure processors
    processors = [
        add_log_level,
        TimeStamper(fmt="iso"),
        add_correlation_id,
        add_app_context,
        format_exception,
        censor_sensitive_data,
    ]
    
    # Add renderer based on format
    if log_format == "json":
        processors.append(CustomJSONRenderer(pretty=pretty))
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Integrate with standard logging
    logging.getLogger().handlers = []
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def get_logger(name: str) -> BoundLogger:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name
    
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


def set_correlation_id(cid: Optional[str] = None) -> str:
    """
    Set correlation ID for current context
    
    Args:
        cid: Correlation ID (generates new one if not provided)
    
    Returns:
        The correlation ID that was set
    """
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID"""
    return correlation_id.get()


class LoggingMiddleware:
    """Middleware for request/response logging"""
    
    def __init__(self, app, correlation_id_header: str = "X-Correlation-ID"):
        self.app = app
        self.correlation_id_header = correlation_id_header
        self.logger = get_logger(__name__)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract or generate correlation ID
        headers = dict(scope.get("headers", []))
        cid = headers.get(self.correlation_id_header.lower().encode(), None)
        if cid:
            cid = cid.decode()
        else:
            cid = str(uuid.uuid4())
        
        set_correlation_id(cid)
        
        # Log request
        self.logger.info(
            "request_started",
            method=scope["method"],
            path=scope["path"],
            query_string=scope.get("query_string", b"").decode(),
            client=scope.get("client"),
        )
        
        start_time = datetime.now()
        status_code = None
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                # Add correlation ID to response headers
                headers = message.setdefault("headers", [])
                headers.append((self.correlation_id_header.encode(), cid.encode()))
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
            
            # Log response
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(
                "request_completed",
                method=scope["method"],
                path=scope["path"],
                status_code=status_code,
                duration=duration,
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                "request_failed",
                method=scope["method"],
                path=scope["path"],
                duration=duration,
                exc_info=sys.exc_info(),
            )
            raise


class TaskLogger:
    """Logger wrapper for Prefect tasks with structured logging"""
    
    def __init__(self, task_name: str):
        self.task_name = task_name
        self.logger = get_logger(f"task.{task_name}")
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"task_started", task=self.task_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type:
            self.logger.error(
                "task_failed",
                task=self.task_name,
                duration=duration,
                exc_info=(exc_type, exc_val, exc_tb)
            )
        else:
            self.logger.info(
                "task_completed",
                task=self.task_name,
                duration=duration
            )
    
    def log(self, level: str, message: str, **kwargs):
        """Log a message with additional context"""
        getattr(self.logger, level)(message, task=self.task_name, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.log("error", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.log("debug", message, **kwargs)