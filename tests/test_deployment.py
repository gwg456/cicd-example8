"""
部署模块测试
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.deployment import DeploymentManager
from src.exceptions import ConfigurationError, NetworkError, DeploymentError


class TestDeploymentManager:
    """部署管理器测试"""
    
    @patch('src.deployment.config')
    def test_init_with_valid_config(self, mock_config):
        """测试有效配置的初始化"""
        mock_config.validate_required_settings.return_value = []
        mock_config.validate_network_settings.return_value = True
        mock_config.apply_prefect_settings.return_value = None
        mock_config.get_config_summary.return_value = {}
        
        manager = DeploymentManager()
        
        assert manager.config == mock_config
        mock_config.apply_prefect_settings.assert_called_once()
        mock_config.validate_required_settings.assert_called_once()
        mock_config.validate_network_settings.assert_called_once()
    
    @patch('src.deployment.config')
    def test_init_with_invalid_config(self, mock_config):
        """测试无效配置的初始化"""
        mock_config.validate_required_settings.return_value = ["PREFECT_API_URL"]
        mock_config.apply_prefect_settings.return_value = None
        
        with pytest.raises(ConfigurationError) as exc_info:
            DeploymentManager()
        
        assert "缺少必需的配置项" in str(exc_info.value)
    
    @patch('src.deployment.config')
    def test_generate_image_tag_with_existing_tag(self, mock_config):
        """测试使用现有标签生成镜像标签"""
        mock_config.validate_required_settings.return_value = []
        mock_config.validate_network_settings.return_value = True
        mock_config.apply_prefect_settings.return_value = None
        mock_config.get_config_summary.return_value = {}
        mock_config.image_repo = "test-repo"
        mock_config.image_tag = "v1.0"
        
        manager = DeploymentManager()
        result = manager._generate_image_tag()
        
        assert result == "test-repo:v1.0"
    
    @patch('src.deployment.config')
    def test_generate_image_tag_without_tag(self, mock_config):
        """测试无现有标签时生成镜像标签"""
        mock_config.validate_required_settings.return_value = []
        mock_config.validate_network_settings.return_value = True
        mock_config.apply_prefect_settings.return_value = None
        mock_config.get_config_summary.return_value = {}
        mock_config.image_repo = "test-repo"
        mock_config.image_tag = None
        
        manager = DeploymentManager()
        result = manager._generate_image_tag()
        
        assert result.startswith("test-repo:v")
        assert len(result.split(":")[1]) > 5  # 检查版本标签格式
    
    @patch('src.deployment.config')
    @patch('src.deployment.get_client')
    async def test_check_prefect_connection_success(self, mock_get_client, mock_config):
        """测试Prefect连接检查成功"""
        mock_config.validate_required_settings.return_value = []
        mock_config.validate_network_settings.return_value = True
        mock_config.apply_prefect_settings.return_value = None
        mock_config.get_config_summary.return_value = {}
        
        mock_client = AsyncMock()
        mock_client.api_healthcheck = AsyncMock(return_value={"status": "ok"})
        mock_get_client.return_value.__aenter__.return_value = mock_client
        
        manager = DeploymentManager()
        result = await manager.check_prefect_connection()
        
        assert result is True
        mock_client.api_healthcheck.assert_called_once()
    
    @patch('src.deployment.config')
    @patch('src.deployment.get_client')
    async def test_check_prefect_connection_failure(self, mock_get_client, mock_config):
        """测试Prefect连接检查失败"""
        mock_config.validate_required_settings.return_value = []
        mock_config.validate_network_settings.return_value = True
        mock_config.apply_prefect_settings.return_value = None
        mock_config.get_config_summary.return_value = {}
        
        mock_get_client.side_effect = Exception("连接失败")
        
        manager = DeploymentManager()
        result = await manager.check_prefect_connection()
        
        assert result is False
    
    @patch('src.deployment.config')
    def test_handle_deployment_error_network(self, mock_config):
        """测试网络错误处理"""
        mock_config.validate_required_settings.return_value = []
        mock_config.validate_network_settings.return_value = True
        mock_config.apply_prefect_settings.return_value = None
        mock_config.get_config_summary.return_value = {}
        mock_config.prefect_api_url = "http://test:4200/api"
        mock_config.api_timeout = 30
        
        manager = DeploymentManager()
        
        with pytest.raises(NetworkError) as exc_info:
            manager._handle_deployment_error(Exception("connecttimeouterror occurred"))
        
        assert "网络连接超时" in str(exc_info.value)
        assert exc_info.value.details["api_url"] == "http://test:4200/api"
    
    @patch('src.deployment.config')
    def test_handle_deployment_error_work_pool(self, mock_config):
        """测试工作池错误处理"""
        mock_config.validate_required_settings.return_value = []
        mock_config.validate_network_settings.return_value = True
        mock_config.apply_prefect_settings.return_value = None
        mock_config.get_config_summary.return_value = {}
        mock_config.work_pool_name = "test-pool"
        
        manager = DeploymentManager()
        
        with pytest.raises(DeploymentError) as exc_info:
            manager._handle_deployment_error(Exception("work_pool not found"))
        
        assert "工作池 'test-pool' 相关错误" in str(exc_info.value)
    
    @patch('src.deployment.config')
    @patch('asyncio.run')
    def test_deploy_hello_flow_sync(self, mock_asyncio_run, mock_config):
        """测试同步部署hello流"""
        mock_config.validate_required_settings.return_value = []
        mock_config.validate_network_settings.return_value = True
        mock_config.apply_prefect_settings.return_value = None
        mock_config.get_config_summary.return_value = {}
        
        mock_asyncio_run.return_value = "deployment-123"
        
        manager = DeploymentManager()
        result = manager.deploy_hello_flow()
        
        assert result == "deployment-123"
        mock_asyncio_run.assert_called_once()
    
    @patch('src.deployment.config')
    def test_deploy_all_success(self, mock_config):
        """测试成功部署所有流"""
        mock_config.validate_required_settings.return_value = []
        mock_config.validate_network_settings.return_value = True
        mock_config.apply_prefect_settings.return_value = None
        mock_config.get_config_summary.return_value = {}
        mock_config.is_container_env = False
        
        manager = DeploymentManager()
        
        with patch.object(manager, 'deploy_hello_flow', return_value="deployment-123"):
            result = manager.deploy_all()
        
        assert result["hello_flow"] == "deployment-123"
    
    @patch('src.deployment.config')
    def test_deploy_all_failure_container_env(self, mock_config):
        """测试容器环境中部署失败"""
        mock_config.validate_required_settings.return_value = []
        mock_config.validate_network_settings.return_value = True
        mock_config.apply_prefect_settings.return_value = None
        mock_config.get_config_summary.return_value = {}
        mock_config.is_container_env = True
        
        manager = DeploymentManager()
        
        with patch.object(manager, 'deploy_hello_flow', side_effect=Exception("部署失败")):
            result = manager.deploy_all()
        
        assert result["status"] == "failed"
        assert "error" in result