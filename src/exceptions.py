"""
自定义异常模块

定义项目特定的异常类，提供更好的错误处理和诊断信息。
"""
from typing import Optional, Dict, Any


class PrefectCICDException(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def get_troubleshooting_info(self) -> Dict[str, Any]:
        """获取故障排除信息"""
        return {
            "error": self.message,
            "details": self.details,
            "troubleshooting": self._get_troubleshooting_tips()
        }
    
    def _get_troubleshooting_tips(self) -> list[str]:
        """获取故障排除提示"""
        return ["检查日志获取更多详细信息"]


class ConfigurationError(PrefectCICDException):
    """配置错误"""
    
    def _get_troubleshooting_tips(self) -> list[str]:
        return [
            "检查环境变量配置是否正确",
            "验证必需的配置项是否已设置",
            "确认配置值的格式和类型正确"
        ]


class NetworkError(PrefectCICDException):
    """网络连接错误"""
    
    def _get_troubleshooting_tips(self) -> list[str]:
        return [
            "检查网络连接状态",
            "验证API URL是否可访问",
            "检查防火墙和代理设置",
            "确认DNS解析正常"
        ]


class DeploymentError(PrefectCICDException):
    """部署错误"""
    
    def _get_troubleshooting_tips(self) -> list[str]:
        return [
            "检查Prefect服务器状态",
            "验证工作池配置",
            "确认Docker镜像可用",
            "检查部署权限设置"
        ]


class ValidationError(PrefectCICDException):
    """验证错误"""
    
    def _get_troubleshooting_tips(self) -> list[str]:
        return [
            "检查输入数据格式",
            "验证必需字段是否存在",
            "确认数据类型正确"
        ]


class TimeoutError(PrefectCICDException):
    """超时错误"""
    
    def _get_troubleshooting_tips(self) -> list[str]:
        return [
            "增加超时配置值",
            "检查网络延迟",
            "确认服务器响应时间",
            "考虑分步骤处理"
        ]


class DockerError(PrefectCICDException):
    """Docker相关错误"""
    
    def _get_troubleshooting_tips(self) -> list[str]:
        return [
            "检查Docker服务状态",
            "验证Docker镜像存在",
            "确认Docker权限设置",
            "检查容器运行环境"
        ]