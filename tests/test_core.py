"""
Tests for core utilities (retry, circuit breaker, exceptions)
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, call

from src.core import (
    AppException,
    ConfigurationError,
    DeploymentError,
    ConnectionError as AppConnectionError,
    TimeoutError as AppTimeoutError,
    RetryableError,
    retry_with_backoff,
    async_retry_with_backoff,
    CircuitBreaker,
    CircuitBreakerOpenError,
    circuit_breaker,
    RetryContext
)


class TestExceptions:
    """Test custom exception classes"""
    
    def test_app_exception_basic(self):
        """Test basic AppException"""
        exc = AppException("Test error", error_code="TEST_ERROR")
        
        assert str(exc) == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.retryable is False
        assert exc.details == {}
    
    def test_app_exception_with_details(self):
        """Test AppException with details"""
        exc = AppException(
            "Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            retryable=True
        )
        
        assert exc.details == {"key": "value"}
        assert exc.retryable is True
    
    def test_app_exception_to_dict(self):
        """Test AppException to_dict method"""
        exc = AppException(
            "Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            retryable=True
        )
        
        result = exc.to_dict()
        assert result["error"] == "TEST_ERROR"
        assert result["message"] == "Test error"
        assert result["details"] == {"key": "value"}
        assert result["retryable"] is True
    
    def test_configuration_error(self):
        """Test ConfigurationError"""
        exc = ConfigurationError("Config error", missing_keys=["KEY1", "KEY2"])
        
        assert exc.error_code == "CONFIGURATION_ERROR"
        assert exc.retryable is False
        assert exc.details["missing_keys"] == ["KEY1", "KEY2"]
    
    def test_deployment_error(self):
        """Test DeploymentError"""
        exc = DeploymentError("Deploy failed", deployment_id="123", flow="test-flow")
        
        assert exc.error_code == "DEPLOYMENT_ERROR"
        assert exc.retryable is True
        assert exc.details["deployment_id"] == "123"
        assert exc.details["flow"] == "test-flow"
    
    def test_connection_error(self):
        """Test ConnectionError"""
        exc = AppConnectionError("Connection failed", service="prefect_api", host="localhost")
        
        assert exc.error_code == "CONNECTION_ERROR"
        assert exc.retryable is True
        assert exc.details["service"] == "prefect_api"
        assert exc.details["host"] == "localhost"
    
    def test_timeout_error(self):
        """Test TimeoutError"""
        exc = AppTimeoutError("Operation timed out", timeout=30, operation="deployment")
        
        assert exc.error_code == "TIMEOUT_ERROR"
        assert exc.retryable is True
        assert exc.details["timeout"] == 30
        assert exc.details["operation"] == "deployment"


class TestRetry:
    """Test retry mechanisms"""
    
    def test_retry_with_backoff_success(self):
        """Test successful retry with backoff"""
        mock_func = Mock(side_effect=[Exception("Error"), Exception("Error"), "Success"])
        
        @retry_with_backoff(max_attempts=3, min_delay=0.01, max_delay=0.1)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "Success"
        assert mock_func.call_count == 3
    
    def test_retry_with_backoff_max_attempts(self):
        """Test retry reaching max attempts"""
        mock_func = Mock(side_effect=Exception("Persistent error"))
        
        @retry_with_backoff(max_attempts=3, min_delay=0.01, max_delay=0.1)
        def test_func():
            return mock_func()
        
        with pytest.raises(Exception) as exc_info:
            test_func()
        
        assert "Persistent error" in str(exc_info.value)
        assert mock_func.call_count == 3
    
    def test_retry_with_backoff_non_retryable(self):
        """Test retry with non-retryable exception"""
        mock_func = Mock(side_effect=ValueError("Non-retryable"))
        
        @retry_with_backoff(
            max_attempts=3,
            min_delay=0.01,
            retryable_exceptions=(RetryableError,)
        )
        def test_func():
            return mock_func()
        
        with pytest.raises(ValueError) as exc_info:
            test_func()
        
        assert "Non-retryable" in str(exc_info.value)
        assert mock_func.call_count == 1  # No retry
    
    def test_retry_with_backoff_callback(self):
        """Test retry with callback"""
        callback = Mock()
        mock_func = Mock(side_effect=[Exception("Error"), "Success"])
        
        @retry_with_backoff(
            max_attempts=3,
            min_delay=0.01,
            on_retry=callback
        )
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "Success"
        assert callback.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_retry_with_backoff_success(self):
        """Test async retry with backoff"""
        mock_func = Mock(side_effect=[Exception("Error"), "Success"])
        
        @async_retry_with_backoff(max_attempts=3, min_delay=0.01, max_delay=0.1)
        async def test_func():
            return mock_func()
        
        result = await test_func()
        assert result == "Success"
        assert mock_func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_async_retry_with_backoff_max_attempts(self):
        """Test async retry reaching max attempts"""
        mock_func = Mock(side_effect=Exception("Persistent error"))
        
        @async_retry_with_backoff(max_attempts=2, min_delay=0.01)
        async def test_func():
            return mock_func()
        
        with pytest.raises(Exception) as exc_info:
            await test_func()
        
        assert "Persistent error" in str(exc_info.value)
        assert mock_func.call_count == 2
    
    def test_retry_context_success(self):
        """Test RetryContext for manual retry control"""
        attempts = []
        
        with RetryContext(max_attempts=3, min_delay=0.01) as ctx:
            while ctx.should_retry():
                try:
                    attempts.append(len(attempts))
                    if len(attempts) < 2:
                        raise Exception("Error")
                    ctx.success()
                    break
                except Exception as e:
                    if ctx.should_retry():
                        ctx.failure(e)
        
        assert len(attempts) == 2
    
    def test_retry_context_max_attempts(self):
        """Test RetryContext reaching max attempts"""
        attempts = []
        
        with pytest.raises(Exception) as exc_info:
            with RetryContext(max_attempts=2, min_delay=0.01) as ctx:
                while ctx.should_retry():
                    try:
                        attempts.append(len(attempts))
                        raise Exception("Persistent error")
                    except Exception as e:
                        ctx.failure(e)
        
        assert "Persistent error" in str(exc_info.value)
        assert len(attempts) == 2


class TestCircuitBreaker:
    """Test circuit breaker pattern"""
    
    def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state"""
        def test_func():
            return "Success"
        
        result = circuit_breaker.call(test_func)
        assert result == "Success"
        assert circuit_breaker.state.value == "closed"
    
    def test_circuit_breaker_open_after_failures(self, circuit_breaker):
        """Test circuit breaker opens after threshold failures"""
        def failing_func():
            raise Exception("Error")
        
        # First failure
        with pytest.raises(Exception):
            circuit_breaker.call(failing_func)
        assert circuit_breaker.state.value == "closed"
        
        # Second failure (threshold reached)
        with pytest.raises(Exception):
            circuit_breaker.call(failing_func)
        assert circuit_breaker.state.value == "open"
        
        # Circuit is open, should reject immediately
        with pytest.raises(CircuitBreakerOpenError):
            circuit_breaker.call(failing_func)
    
    def test_circuit_breaker_half_open_recovery(self, circuit_breaker):
        """Test circuit breaker recovery to half-open state"""
        def failing_func():
            raise Exception("Error")
        
        def success_func():
            return "Success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                circuit_breaker.call(failing_func)
        
        assert circuit_breaker.state.value == "open"
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should transition to half-open and allow test
        result = circuit_breaker.call(success_func)
        assert result == "Success"
        assert circuit_breaker.state.value == "half_open"
        
        # Another success should close the circuit
        result = circuit_breaker.call(success_func)
        assert result == "Success"
        assert circuit_breaker.state.value == "closed"
    
    def test_circuit_breaker_half_open_failure(self, circuit_breaker):
        """Test circuit breaker failure in half-open state"""
        def failing_func():
            raise Exception("Error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                circuit_breaker.call(failing_func)
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Failure in half-open should reopen circuit
        with pytest.raises(Exception):
            circuit_breaker.call(failing_func)
        assert circuit_breaker.state.value == "open"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_async(self, circuit_breaker):
        """Test circuit breaker with async functions"""
        async def async_func():
            return "Async Success"
        
        result = await circuit_breaker.async_call(async_func)
        assert result == "Async Success"
    
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker as decorator"""
        call_count = [0]
        
        @circuit_breaker(failure_threshold=2, recovery_timeout=1)
        def test_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Error")
            return "Success"
        
        # First two calls fail and open circuit
        with pytest.raises(Exception):
            test_func()
        with pytest.raises(Exception):
            test_func()
        
        # Circuit is open
        with pytest.raises(CircuitBreakerOpenError):
            test_func()
    
    def test_circuit_breaker_metrics(self, circuit_breaker):
        """Test circuit breaker metrics"""
        def test_func():
            return "Success"
        
        def failing_func():
            raise Exception("Error")
        
        # Some successful calls
        for _ in range(3):
            circuit_breaker.call(test_func)
        
        # Some failed calls
        with pytest.raises(Exception):
            circuit_breaker.call(failing_func)
        
        metrics = circuit_breaker.get_metrics()
        
        assert metrics["name"] == "test_breaker"
        assert metrics["total_calls"] == 4
        assert metrics["total_successes"] == 3
        assert metrics["total_failures"] == 1
        assert metrics["success_rate"] == 75.0
    
    def test_circuit_breaker_reset(self, circuit_breaker):
        """Test manual circuit breaker reset"""
        def failing_func():
            raise Exception("Error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                circuit_breaker.call(failing_func)
        
        assert circuit_breaker.state.value == "open"
        
        # Manual reset
        circuit_breaker.reset()
        assert circuit_breaker.state.value == "closed"
        assert circuit_breaker._failure_count == 0