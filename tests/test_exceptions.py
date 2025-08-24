"""
异常模块测试
"""
import pytest
from src.exceptions import (
    PrefectCICDException, ConfigurationError, NetworkError,
    DeploymentError, ValidationError, TimeoutError, DockerError
)


class TestPrefectCICDException:
    """基础异常类测试"""
    
    def test_basic_exception(self):
        """测试基础异常"""
        exc = PrefectCICDException("测试错误")
        
        assert str(exc) == "测试错误"
        assert exc.message == "测试错误"
        assert exc.details == {}
    
    def test_exception_with_details(self):
        """测试带详细信息的异常"""
        details = {"key": "value", "error_code": 500}
        exc = PrefectCICDException("测试错误", details)
        
        assert exc.details == details
    
    def test_get_troubleshooting_info(self):
        """测试故障排除信息"""
        exc = PrefectCICDException("测试错误")
        info = exc.get_troubleshooting_info()
        
        assert isinstance(info, dict)
        assert "error" in info
        assert "details" in info
        assert "troubleshooting" in info
        assert info["error"] == "测试错误"


class TestSpecificExceptions:
    """特定异常类测试"""
    
    def test_configuration_error(self):
        """测试配置错误"""
        exc = ConfigurationError("配置错误")
        tips = exc._get_troubleshooting_tips()
        
        assert "检查环境变量配置是否正确" in tips
    
    def test_network_error(self):
        """测试网络错误"""
        exc = NetworkError("网络错误")
        tips = exc._get_troubleshooting_tips()
        
        assert "检查网络连接状态" in tips
    
    def test_deployment_error(self):
        """测试部署错误"""
        exc = DeploymentError("部署错误")
        tips = exc._get_troubleshooting_tips()
        
        assert "检查Prefect服务器状态" in tips
    
    def test_validation_error(self):
        """测试验证错误"""
        exc = ValidationError("验证错误")
        tips = exc._get_troubleshooting_tips()
        
        assert "检查输入数据格式" in tips
    
    def test_timeout_error(self):
        """测试超时错误"""
        exc = TimeoutError("超时错误")
        tips = exc._get_troubleshooting_tips()
        
        assert "增加超时配置值" in tips
    
    def test_docker_error(self):
        """测试Docker错误"""
        exc = DockerError("Docker错误")
        tips = exc._get_troubleshooting_tips()
        
        assert "检查Docker服务状态" in tips