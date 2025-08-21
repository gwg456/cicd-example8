"""
Pytest配置文件和共享fixtures
"""
import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from prefect.testing.utilities import prefect_test_harness

from config import Config


@pytest.fixture(scope="session", autouse=True)
def prefect_test_session():
    """为整个测试会话设置Prefect测试环境"""
    with prefect_test_harness():
        yield


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_config() -> Config:
    """创建测试用的配置对象"""
    return Config(
        prefect_api_url="http://test-api:4200/api",
        work_pool_name="test-pool",
        image_repo="test/repo",
        image_tag="test-tag",
        log_level="DEBUG",
        environment="test",
        deploy_mode=False,
        schedule_interval=60,
        api_timeout=30,
        deployment_timeout=30,
    )


@pytest.fixture
def mock_env_vars():
    """模拟环境变量"""
    env_vars = {
        "PREFECT_API_URL": "http://test-api:4200/api",
        "WORK_POOL_NAME": "test-pool",
        "IMAGE_REPO": "test/repo",
        "IMAGE_TAG": "test-tag",
        "LOG_LEVEL": "DEBUG",
        "ENVIRONMENT": "test",
        "DEPLOY_MODE": "false",
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_prefect_client():
    """模拟Prefect客户端"""
    mock_client = Mock()
    mock_client.api_healthcheck.return_value = {"status": "ok"}
    
    with patch("prefect.client.orchestration.get_client") as mock_get_client:
        mock_get_client.return_value.__aenter__.return_value = mock_client
        mock_get_client.return_value.__aexit__.return_value = None
        yield mock_client


@pytest.fixture
def mock_docker():
    """模拟Docker相关操作"""
    with patch("docker.from_env") as mock_docker_client:
        mock_client = Mock()
        mock_docker_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_pdf_path(temp_dir: Path) -> Path:
    """创建示例PDF文件路径"""
    pdf_path = temp_dir / "sample.pdf"
    # 创建一个空文件作为示例
    pdf_path.touch()
    return pdf_path


class MockFlow:
    """模拟Prefect Flow对象"""
    
    def __init__(self, name: str = "test-flow"):
        self.name = name
        self.deployed = False
        self.deployment_id = f"deployment-{name}-123"
    
    def deploy(self, **kwargs):
        """模拟部署方法"""
        self.deployed = True
        return self.deployment_id


@pytest.fixture
def mock_flow():
    """创建模拟的Flow对象"""
    return MockFlow()


@pytest.fixture
def mock_successful_deployment():
    """模拟成功的部署"""
    def _deploy(**kwargs):
        return "deployment-123-success"
    
    return _deploy


@pytest.fixture
def mock_failed_deployment():
    """模拟失败的部署"""
    def _deploy(**kwargs):
        raise Exception("Deployment failed")
    
    return _deploy
