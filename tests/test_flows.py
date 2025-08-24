"""
流模块测试
"""
import pytest
from unittest.mock import patch, MagicMock
from src.flows import hello_flow, health_check_flow, generate_greeting, sleep_task


class TestTasks:
    """任务测试"""
    
    def test_generate_greeting_default(self):
        """测试默认问候语生成"""
        result = generate_greeting()
        assert result == "Hello World! This run was scheduled via Interval!"
    
    def test_generate_greeting_custom_name(self):
        """测试自定义名称问候语"""
        result = generate_greeting("Alice")
        assert result == "Hello Alice! This run was scheduled via Interval!"
    
    @patch('time.sleep')
    def test_sleep_task(self, mock_sleep):
        """测试休眠任务"""
        sleep_task(10)
        mock_sleep.assert_called_once_with(10)


class TestFlows:
    """流测试"""
    
    @patch('src.flows.sleep_task')
    @patch('src.flows.generate_greeting')
    def test_hello_flow(self, mock_greeting, mock_sleep):
        """测试hello流"""
        mock_greeting.return_value = "Test greeting"
        
        result = hello_flow("TestUser")
        
        mock_greeting.assert_called_once_with("TestUser")
        mock_sleep.assert_called_once()
        assert result == "Test greeting"
    
    def test_health_check_flow(self):
        """测试健康检查流"""
        result = health_check_flow()
        
        assert isinstance(result, dict)
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "message" in result
        assert result["message"] == "Flow is running successfully"