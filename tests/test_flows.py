"""
Tests for Prefect flows
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.flows import (
    generate_greeting,
    process_data,
    sleep_task,
    hello_flow,
    health_check_flow,
    data_pipeline_flow
)


class TestTasks:
    """Test individual Prefect tasks"""
    
    def test_generate_greeting_default(self):
        """Test greeting generation with default name"""
        result = generate_greeting()
        assert result == "Hello World! This run was scheduled via Prefect."
    
    def test_generate_greeting_custom_name(self):
        """Test greeting generation with custom name"""
        result = generate_greeting("Alice")
        assert result == "Hello Alice! This run was scheduled via Prefect."
    
    def test_generate_greeting_invalid_input(self):
        """Test greeting generation with invalid input"""
        # Empty string
        result = generate_greeting("")
        assert "World" in result
        
        # None value
        result = generate_greeting(None)
        assert "World" in result
        
        # Very long name (should be truncated)
        long_name = "A" * 200
        result = generate_greeting(long_name)
        assert len(result) < 150
    
    def test_process_data_success(self, sample_data):
        """Test successful data processing"""
        result = process_data(sample_data)
        
        assert result["status"] == "processed"
        assert "processed_at" in result
        assert result["item_count"] == len(sample_data)
        assert result["original_keys"] == list(sample_data.keys())
    
    def test_process_data_high_priority(self):
        """Test high priority data processing"""
        data = {"priority": "high", "value": 100}
        result = process_data(data)
        
        assert result["fast_track"] is True
    
    def test_process_data_normal_priority(self):
        """Test normal priority data processing"""
        data = {"priority": "normal", "value": 100}
        result = process_data(data)
        
        assert "fast_track" not in result or result["fast_track"] is False
    
    @patch("time.sleep")
    def test_sleep_task_valid_duration(self, mock_sleep):
        """Test sleep task with valid duration"""
        sleep_task(10)
        mock_sleep.assert_called_once_with(10)
    
    @patch("time.sleep")
    def test_sleep_task_negative_duration(self, mock_sleep):
        """Test sleep task with negative duration"""
        sleep_task(-5)
        # Should use default duration
        mock_sleep.assert_called_once_with(20)
    
    @patch("time.sleep")
    def test_sleep_task_excessive_duration(self, mock_sleep):
        """Test sleep task with excessive duration"""
        sleep_task(500)
        # Should cap at 300 seconds
        mock_sleep.assert_called_once_with(300)


class TestFlows:
    """Test Prefect flows"""
    
    @patch("src.flows.sleep_task")
    @patch("src.flows.process_data")
    @patch("src.flows.generate_greeting")
    def test_hello_flow_basic(self, mock_greeting, mock_process, mock_sleep):
        """Test basic hello flow execution"""
        mock_greeting.return_value = "Hello Test!"
        mock_process.return_value = {"status": "processed"}
        
        result = hello_flow(name="Test", include_processing=True)
        
        assert result["status"] == "success"
        assert result["greeting"] == "Hello Test!"
        assert "processed_data" in result
        assert "started_at" in result
        assert "completed_at" in result
        
        mock_greeting.assert_called_once_with("Test")
        mock_process.assert_called_once()
        mock_sleep.assert_called_once()
    
    @patch("src.flows.sleep_task")
    @patch("src.flows.generate_greeting")
    def test_hello_flow_without_processing(self, mock_greeting, mock_sleep):
        """Test hello flow without data processing"""
        mock_greeting.return_value = "Hello Test!"
        
        result = hello_flow(name="Test", include_processing=False)
        
        assert result["status"] == "success"
        assert "processed_data" not in result
        
        mock_greeting.assert_called_once_with("Test")
        mock_sleep.assert_called_once()
    
    @patch("src.flows.generate_greeting")
    def test_hello_flow_error_handling(self, mock_greeting):
        """Test hello flow error handling"""
        mock_greeting.side_effect = Exception("Test error")
        
        with pytest.raises(Exception) as exc_info:
            hello_flow(name="Test")
        
        assert "Test error" in str(exc_info.value)
    
    @patch("psutil.disk_usage")
    @patch("psutil.virtual_memory")
    @patch("psutil.cpu_percent")
    def test_health_check_flow_healthy(self, mock_cpu, mock_memory, mock_disk):
        """Test health check flow when system is healthy"""
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0)
        mock_disk.return_value = Mock(percent=70.0)
        
        with patch("asyncio.run", return_value=None):
            result = health_check_flow()
        
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "checks" in result
        assert result["checks"]["system"]["status"] == "healthy"
    
    @patch("psutil.disk_usage")
    @patch("psutil.virtual_memory")
    @patch("psutil.cpu_percent")
    def test_health_check_flow_degraded(self, mock_cpu, mock_memory, mock_disk):
        """Test health check flow when system is degraded"""
        mock_cpu.return_value = 85.0  # High CPU
        mock_memory.return_value = Mock(percent=60.0)
        mock_disk.return_value = Mock(percent=70.0)
        
        with patch("asyncio.run", return_value=None):
            result = health_check_flow()
        
        assert result["status"] == "degraded"
        assert result["checks"]["system"]["status"] == "degraded"
    
    @patch("psutil.cpu_percent")
    def test_health_check_flow_error(self, mock_cpu):
        """Test health check flow error handling"""
        mock_cpu.side_effect = Exception("System error")
        
        result = health_check_flow()
        
        assert result["status"] == "unhealthy"
        assert "error" in result
    
    @patch("src.flows.process_data")
    def test_data_pipeline_flow(self, mock_process):
        """Test data pipeline flow"""
        mock_process.return_value = {"status": "processed"}
        
        result = data_pipeline_flow(batch_size=10, parallel_workers=2)
        
        assert result["status"] == "success"
        assert result["batch_size"] == 10
        assert result["parallel_workers"] == 2
        assert result["batches_processed"] == 5
        assert result["items_processed"] == 50
        
        # Verify process_data was called for each batch
        assert mock_process.call_count == 5
    
    @patch("src.flows.process_data")
    def test_data_pipeline_flow_error(self, mock_process):
        """Test data pipeline flow error handling"""
        mock_process.side_effect = Exception("Processing error")
        
        with pytest.raises(Exception) as exc_info:
            data_pipeline_flow(batch_size=10)
        
        assert "Processing error" in str(exc_info.value)


class TestFlowIntegration:
    """Integration tests for flows"""
    
    @pytest.mark.integration
    def test_hello_flow_end_to_end(self):
        """Test complete hello flow execution"""
        with patch("time.sleep"):  # Speed up test
            result = hello_flow(name="Integration Test")
        
        assert result["status"] == "success"
        assert "Hello Integration Test!" in result["greeting"]
        assert result["parameters"]["name"] == "Integration Test"
    
    @pytest.mark.integration
    def test_health_check_flow_end_to_end(self):
        """Test complete health check flow execution"""
        result = health_check_flow()
        
        assert "status" in result
        assert "timestamp" in result
        assert "checks" in result
        assert result["status"] in ["healthy", "degraded", "unhealthy"]
    
    @pytest.mark.integration
    @patch("time.sleep")
    def test_data_pipeline_flow_end_to_end(self, mock_sleep):
        """Test complete data pipeline flow execution"""
        result = data_pipeline_flow(batch_size=5, parallel_workers=2)
        
        assert result["status"] == "success"
        assert result["items_processed"] == 25  # 5 batches * 5 items