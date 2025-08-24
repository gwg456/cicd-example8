"""
统一日志记录模块

提供结构化的日志记录功能，支持不同的日志级别和格式。
"""
import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        # 基础日志信息
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # 添加额外信息
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, indent=None)


class PrefectCICDLogger:
    """项目日志记录器"""
    
    def __init__(self, name: str, level: str = "INFO", structured: bool = False):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers(structured)
    
    def _setup_handlers(self, structured: bool):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        
        if structured:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, **extra):
        """记录信息日志"""
        self._log_with_extra(logging.INFO, message, extra)
    
    def warning(self, message: str, **extra):
        """记录警告日志"""
        self._log_with_extra(logging.WARNING, message, extra)
    
    def error(self, message: str, **extra):
        """记录错误日志"""
        self._log_with_extra(logging.ERROR, message, extra)
    
    def debug(self, message: str, **extra):
        """记录调试日志"""
        self._log_with_extra(logging.DEBUG, message, extra)
    
    def _log_with_extra(self, level: int, message: str, extra: Dict[str, Any]):
        """使用额外数据记录日志"""
        if extra:
            self.logger.log(level, message, extra={"extra_data": extra})
        else:
            self.logger.log(level, message)
    
    def log_config(self, config_summary: Dict[str, Any]):
        """记录配置信息"""
        self.info("应用配置加载完成", config=config_summary)
    
    def log_deployment_start(self, deployment_name: str, image: str):
        """记录部署开始"""
        self.info(
            f"开始部署: {deployment_name}",
            deployment_name=deployment_name,
            image=image,
            phase="deployment_start"
        )
    
    def log_deployment_success(self, deployment_name: str, deployment_id: str):
        """记录部署成功"""
        self.info(
            f"部署成功: {deployment_name}",
            deployment_name=deployment_name,
            deployment_id=deployment_id,
            phase="deployment_success"
        )
    
    def log_deployment_error(self, deployment_name: str, error: Exception):
        """记录部署错误"""
        self.error(
            f"部署失败: {deployment_name}",
            deployment_name=deployment_name,
            error_type=type(error).__name__,
            error_message=str(error),
            phase="deployment_error",
            exc_info=True
        )
    
    def log_flow_execution(self, flow_name: str, status: str, **details):
        """记录流执行信息"""
        self.info(
            f"流执行 {status}: {flow_name}",
            flow_name=flow_name,
            status=status,
            phase="flow_execution",
            **details
        )


def get_logger(name: str, level: Optional[str] = None, structured: bool = False) -> PrefectCICDLogger:
    """获取项目日志记录器"""
    from config import config
    
    log_level = level or config.log_level
    return PrefectCICDLogger(name, log_level, structured)