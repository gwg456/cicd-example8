"""
流程模块的单元测试
"""
import time
from unittest.mock import patch

import pytest
from prefect.testing.utilities import prefect_test_harness

from src.flows import (
    generate_greeting,
    health_check_flow,
    hello_flow,
    process_pdf,
    process_pdf_flow,
    sleep_task,
)


class TestTasks:
    """测试任务函数"""
    
    def test_generate_greeting_default(self):
        """测试默认问候语生成"""
        result = generate_greeting()
        assert result == "Hello World! This run was scheduled via Interval!"
    
    def test_generate_greeting_custom_name(self):
        """测试自定义名称的问候语生成"""
        result = generate_greeting("Alice")
        assert result == "Hello Alice! This run was scheduled via Interval!"
    
    def test_generate_greeting_empty_name(self):
        """测试空名称的问候语生成"""
        result = generate_greeting("")
        assert result == "Hello ! This run was scheduled via Interval!"
    
    @patch("time.sleep")
    def test_sleep_task_default(self, mock_sleep):
        """测试默认休眠任务"""
        sleep_task()
        mock_sleep.assert_called_once_with(20)
    
    @patch("time.sleep")
    def test_sleep_task_custom_duration(self, mock_sleep):
        """测试自定义时长的休眠任务"""
        sleep_task(5)
        mock_sleep.assert_called_once_with(5)
    
    @patch("time.sleep")
    def test_process_pdf_default(self, mock_sleep):
        """测试默认PDF处理任务"""
        with patch("time.time", return_value=1000.0):
            result = process_pdf()
            
            # 验证返回结果格式
            assert "example.pdf" in result
            assert "处理完成" in result
            assert "耗时" in result
            
            # 验证sleep被调用
            mock_sleep.assert_called_once()
    
    @patch("time.sleep")
    def test_process_pdf_custom_file(self, mock_sleep):
        """测试自定义文件的PDF处理任务"""
        with patch("time.time", return_value=1000.0):
            result = process_pdf("custom.pdf")
            
            assert "custom.pdf" in result
            assert "处理完成" in result
            mock_sleep.assert_called_once()


class TestFlows:
    """测试流程函数"""
    
    def test_hello_flow_default(self):
        """测试默认问候流程"""
        with patch("src.flows.sleep_task") as mock_sleep:
            result = hello_flow()
            
            assert result == "Hello World! This run was scheduled via Interval!"
            mock_sleep.assert_called_once()
    
    def test_hello_flow_custom_name(self):
        """测试自定义名称的问候流程"""
        with patch("src.flows.sleep_task") as mock_sleep:
            result = hello_flow("Bob")
            
            assert result == "Hello Bob! This run was scheduled via Interval!"
            mock_sleep.assert_called_once()
    
    def test_health_check_flow(self):
        """测试健康检查流程"""
        result = health_check_flow()
        
        assert isinstance(result, dict)
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "message" in result
        assert result["message"] == "Flow is running successfully"
        
        # 验证时间戳格式
        import datetime
        timestamp = datetime.datetime.fromisoformat(result["timestamp"])
        assert isinstance(timestamp, datetime.datetime)
    
    def test_process_pdf_flow(self):
        """测试PDF处理流程"""
        with patch("src.flows.process_pdf") as mock_process:
            mock_process.return_value = "处理完成"
            
            # 由于这是一个flow，我们需要在测试环境中运行
            process_pdf_flow()
            
            # 验证process_pdf被调用
            mock_process.assert_called_once_with("通信网络安全防护公益培训.pdf")


class TestFlowIntegration:
    """测试流程集成"""
    
    @pytest.mark.slow
    def test_hello_flow_full_execution(self):
        """测试完整的问候流程执行（慢速测试）"""
        # 使用较短的休眠时间进行测试
        with patch("src.flows.sleep_task") as mock_sleep:
            mock_sleep.return_value = None  # 跳过实际休眠
            
            start_time = time.time()
            result = hello_flow("TestUser")
            end_time = time.time()
            
            # 验证结果
            assert result == "Hello TestUser! This run was scheduled via Interval!"
            
            # 验证执行时间合理（应该很快，因为我们mock了sleep）
            assert end_time - start_time < 1.0
    
    def test_flow_error_handling(self):
        """测试流程错误处理"""
        with patch("src.flows.generate_greeting") as mock_greeting:
            mock_greeting.side_effect = Exception("Test error")
            
            # 流程应该传播异常
            with pytest.raises(Exception, match="Test error"):
                hello_flow()
    
    def test_multiple_flows_execution(self):
        """测试多个流程的执行"""
        # 测试多个流程可以同时运行而不冲突
        with patch("src.flows.sleep_task"):
            result1 = hello_flow("User1")
            result2 = hello_flow("User2")
            health_result = health_check_flow()
            
            assert "User1" in result1
            assert "User2" in result2
            assert health_result["status"] == "healthy"


class TestTaskParameters:
    """测试任务参数处理"""
    
    def test_generate_greeting_type_validation(self):
        """测试问候语生成的类型验证"""
        # 测试不同类型的输入
        assert generate_greeting(123) == "Hello 123! This run was scheduled via Interval!"
        assert generate_greeting(None) == "Hello None! This run was scheduled via Interval!"
    
    def test_sleep_task_parameter_validation(self):
        """测试休眠任务的参数验证"""
        with patch("time.sleep") as mock_sleep:
            # 测试负数（应该仍然调用sleep，由time.sleep处理）
            sleep_task(-1)
            mock_sleep.assert_called_with(-1)
            
            # 测试零
            sleep_task(0)
            mock_sleep.assert_called_with(0)
            
            # 测试浮点数
            sleep_task(1.5)
            mock_sleep.assert_called_with(1.5)
    
    def test_process_pdf_parameter_validation(self):
        """测试PDF处理任务的参数验证"""
        with patch("time.sleep"):
            with patch("time.time", return_value=1000.0):
                # 测试空字符串
                result = process_pdf("")
                assert "文件 '' 处理完成" in result
                
                # 测试特殊字符
                result = process_pdf("file with spaces.pdf")
                assert "file with spaces.pdf" in result
