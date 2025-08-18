"""
Pytest configuration and fixtures
"""
import os
import sys
import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Generator, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["PREFECT_API_URL"] = "http://test-server:4200/api"
os.environ["DEPLOY_MODE"] = "false"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    from src.config.settings import Settings, Environment
    
    settings = Settings(
        environment=Environment.TESTING,
        prefect_api_url="http://test-server:4200/api",
        work_pool_name="test-pool",
        image_repo="test-repo",
        image_tag="test-tag",
        deploy_mode=False,
        enable_auth=False,
        enable_metrics=False,
    )
    
    with patch("src.config.get_settings", return_value=settings):
        yield settings


@pytest.fixture
def mock_prefect_client():
    """Mock Prefect client"""
    with patch("prefect.client.orchestration.get_client") as mock_get_client:
        mock_client = Mock()
        mock_client.api_healthcheck = Mock(return_value=asyncio.coroutine(lambda: None)())
        mock_client.read_work_pools = Mock(return_value=asyncio.coroutine(lambda: [Mock(name="test-pool")])())
        
        mock_context = Mock()
        mock_context.__aenter__ = Mock(return_value=asyncio.coroutine(lambda: mock_client)())
        mock_context.__aexit__ = Mock(return_value=asyncio.coroutine(lambda *args: None)())
        
        mock_get_client.return_value = mock_context
        yield mock_client


@pytest.fixture
def mock_metrics():
    """Mock metrics collector"""
    from unittest.mock import MagicMock
    
    mock = MagicMock()
    with patch("src.monitoring.metrics.metrics", mock):
        yield mock


@pytest.fixture
def sample_data():
    """Sample data for testing"""
    return {
        "user": "test_user",
        "timestamp": "2024-01-01T00:00:00",
        "priority": "normal",
        "items": [
            {"id": 1, "value": 0.5},
            {"id": 2, "value": 0.7},
            {"id": 3, "value": 0.3},
        ]
    }


@pytest.fixture
def deployment_manager(mock_settings, mock_prefect_client):
    """Create deployment manager for testing"""
    from src.deployment import DeploymentManager
    
    manager = DeploymentManager()
    return manager


@pytest.fixture
def circuit_breaker():
    """Create circuit breaker for testing"""
    from src.core.circuit_breaker import CircuitBreaker
    
    return CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=1,
        expected_exception=Exception,
        name="test_breaker"
    )


@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset all circuit breakers before each test"""
    from src.core.circuit_breaker import reset_all_circuit_breakers
    
    reset_all_circuit_breakers()
    yield
    reset_all_circuit_breakers()


@pytest.fixture
def temp_env_vars():
    """Temporarily set environment variables"""
    original_env = os.environ.copy()
    
    def _set_env(**kwargs):
        for key, value in kwargs.items():
            os.environ[key] = str(value)
    
    yield _set_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_time():
    """Mock time for testing timeouts and delays"""
    with patch("time.time") as mock_time_func:
        mock_time_func.return_value = 1000.0
        with patch("time.sleep") as mock_sleep:
            yield {"time": mock_time_func, "sleep": mock_sleep}


@pytest.fixture
def capture_logs():
    """Capture log messages for testing"""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    yield log_capture
    
    logger.removeHandler(handler)