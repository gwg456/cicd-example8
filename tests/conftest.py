"""
pytest配置文件
"""
import pytest
import os
import sys
from unittest.mock import MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_config():
    """模拟配置对象"""
    from config import Config
    
    config = Config()
    config.prefect_api_url = "http://test-api:4200/api"
    config.work_pool_name = "test-pool"
    config.image_repo = "test-repo"
    config.image_tag = "test-tag"
    config.deploy_mode = False
    config.api_timeout = 30
    config.deployment_timeout = 60
    config.schedule_interval = 3600
    
    return config


@pytest.fixture
def mock_prefect_client():
    """模拟Prefect客户端"""
    client = MagicMock()
    client.api_healthcheck.return_value = {"status": "ok"}
    return client


@pytest.fixture
def mock_deployment_id():
    """模拟部署ID"""
    return "test-deployment-123"