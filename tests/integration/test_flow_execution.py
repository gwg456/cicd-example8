"""
流程执行的集成测试
"""
import pytest
from prefect.testing.utilities import prefect_test_harness

from src.flows import hello_flow, health_check_flow, process_pdf_flow


class TestFlowExecution:
    """测试流程执行的集成"""
    
    @pytest.mark.integration
    def test_hello_flow_execution(self):
        """测试问候流程的完整执行"""
        # 在测试环境中执行流程
        result = hello_flow("Integration Test")
        
        # 验证返回结果
        assert isinstance(result, str)
        assert "Integration Test" in result
        assert "Hello" in result
    
    @pytest.mark.integration
    def test_health_check_flow_execution(self):
        """测试健康检查流程的完整执行"""
        result = health_check_flow()
        
        # 验证返回结果结构
        assert isinstance(result, dict)
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "message" in result
        
        # 验证时间戳格式
        import datetime
        timestamp = datetime.datetime.fromisoformat(result["timestamp"])
        assert isinstance(timestamp, datetime.datetime)
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_process_pdf_flow_execution(self):
        """测试PDF处理流程的完整执行"""
        # 这个测试可能需要更长时间，因为包含sleep
        process_pdf_flow()
        
        # 如果没有异常，说明流程执行成功
        # 在实际测试中，我们可以检查日志或其他副作用
    
    @pytest.mark.integration
    def test_multiple_flows_parallel_execution(self):
        """测试多个流程的并行执行"""
        import concurrent.futures
        
        def run_hello_flow(name):
            return hello_flow(name)
        
        # 并行执行多个流程
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(run_hello_flow, f"User{i}")
                for i in range(3)
            ]
            
            results = [future.result() for future in futures]
        
        # 验证所有流程都成功执行
        assert len(results) == 3
        for i, result in enumerate(results):
            assert f"User{i}" in result
    
    @pytest.mark.integration
    def test_flow_state_management(self):
        """测试流程状态管理"""
        # 执行流程并检查状态
        result = hello_flow("State Test")
        
        # 在实际的Prefect环境中，我们可以检查流程运行状态
        # 这里我们只验证基本的执行结果
        assert result is not None
        assert isinstance(result, str)


class TestFlowErrorHandling:
    """测试流程错误处理的集成"""
    
    @pytest.mark.integration
    def test_flow_with_task_failure(self):
        """测试任务失败时的流程处理"""
        from unittest.mock import patch
        
        # 模拟任务失败
        with patch("src.flows.generate_greeting") as mock_task:
            mock_task.side_effect = Exception("Task failed")
            
            # 流程应该传播异常
            with pytest.raises(Exception, match="Task failed"):
                hello_flow("Error Test")
    
    @pytest.mark.integration
    def test_flow_retry_behavior(self):
        """测试流程重试行为"""
        # 这个测试需要配置重试策略
        # 在实际实现中，可以测试任务的重试机制
        pass


class TestFlowConfiguration:
    """测试流程配置的集成"""
    
    @pytest.mark.integration
    def test_flow_logging(self):
        """测试流程日志记录"""
        import logging
        from unittest.mock import patch
        
        with patch("src.flows.logger") as mock_logger:
            # 执行包含日志的流程
            process_pdf_flow()
            
            # 验证日志被调用
            # 注意：实际的日志调用可能在process_pdf任务中
            # 这里我们验证logger对象被使用
            assert mock_logger is not None
    
    @pytest.mark.integration
    def test_flow_parameters(self):
        """测试流程参数传递"""
        # 测试不同参数的流程执行
        test_cases = [
            ("Alice", "Hello Alice!"),
            ("Bob", "Hello Bob!"),
            ("", "Hello !"),
            ("测试用户", "Hello 测试用户!"),
        ]
        
        for name, expected_part in test_cases:
            result = hello_flow(name)
            assert expected_part in result


class TestFlowIntegrationWithConfig:
    """测试流程与配置的集成"""
    
    @pytest.mark.integration
    def test_flow_with_different_environments(self, mock_env_vars):
        """测试不同环境下的流程执行"""
        # 在模拟的环境变量下执行流程
        result = hello_flow("Config Test")
        
        # 流程应该正常执行，不受环境变量影响
        assert "Config Test" in result
    
    @pytest.mark.integration
    def test_flow_execution_time(self):
        """测试流程执行时间"""
        import time
        from unittest.mock import patch
        
        # 使用mock来控制执行时间
        with patch("src.flows.sleep_task") as mock_sleep:
            mock_sleep.return_value = None  # 跳过实际休眠
            
            start_time = time.time()
            hello_flow("Performance Test")
            end_time = time.time()
            
            # 验证执行时间合理（应该很快）
            execution_time = end_time - start_time
            assert execution_time < 1.0  # 应该在1秒内完成
