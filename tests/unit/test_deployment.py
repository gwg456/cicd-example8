"""
部署模块的单元测试
"""
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.deployment import DeploymentManager


class TestDeploymentManager:
    """测试部署管理器"""
    
    def test_init(self, mock_config):
        """测试初始化"""
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            assert manager.config == mock_config
    
    def test_generate_image_tag_with_provided_tag(self, mock_config):
        """测试使用提供的镜像标签"""
        mock_config.image_tag = "v1.0.0"
        mock_config.image_repo = "test/repo"
        
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            tag = manager._generate_image_tag()
            
            assert tag == "test/repo:v1.0.0"
    
    def test_generate_image_tag_without_provided_tag(self, mock_config):
        """测试生成新的镜像标签"""
        mock_config.image_tag = None
        mock_config.image_repo = "test/repo"
        
        with patch("src.deployment.config", mock_config):
            with patch("datetime.datetime") as mock_datetime:
                mock_now = Mock()
                mock_now.strftime.return_value = "202312011200"
                mock_datetime.now.return_value = mock_now
                
                manager = DeploymentManager()
                tag = manager._generate_image_tag()
                
                assert tag == "test/repo:v202312011200"
    
    def test_get_base_env_vars(self, mock_config):
        """测试获取基础环境变量"""
        mock_config.log_level = "DEBUG"
        mock_config.environment = "test"
        mock_config.api_timeout = 60
        
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            env_vars = manager._get_base_env_vars()
            
            expected_vars = {
                "LOG_LEVEL": "DEBUG",
                "ENVIRONMENT": "test",
                "PYTHONUNBUFFERED": "1",
                "PREFECT_LOGGING_LEVEL": "DEBUG",
                "PREFECT_API_RESPONSE_TIMEOUT": "60",
                "PREFECT_API_REQUEST_TIMEOUT": "60",
            }
            
            assert env_vars == expected_vars
    
    def test_get_docker_job_variables_container_env(self, mock_config):
        """测试容器环境下的Docker作业变量"""
        mock_config.is_container_env = True
        
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            with patch.object(manager, "_get_base_env_vars") as mock_base_env:
                mock_base_env.return_value = {"TEST": "value"}
                
                variables = manager._get_docker_job_variables()
                
                assert variables == {"env": {"TEST": "value"}}
    
    def test_get_docker_job_variables_local_env(self, mock_config):
        """测试本地环境下的Docker作业变量"""
        mock_config.is_container_env = False
        
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            with patch.object(manager, "_get_base_env_vars") as mock_base_env:
                mock_base_env.return_value = {"TEST": "value"}
                
                with patch("tempfile.mkdtemp") as mock_mkdtemp:
                    mock_mkdtemp.return_value = "/tmp/test"
                    
                    variables = manager._get_docker_job_variables()
                    
                    # 验证包含基础环境变量
                    assert "env.TEST" in variables
                    assert variables["env.TEST"] == "value"
                    
                    # 验证包含Docker特定配置
                    assert "env.DOCKER_CLIENT_TIMEOUT" in variables
                    assert "env.PREFECT_DOCKER_VOLUME_MOUNTS" in variables
    
    @pytest.mark.asyncio
    async def test_check_prefect_connection_success(self, mock_config, mock_prefect_client):
        """测试Prefect连接检查成功"""
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            result = await manager.check_prefect_connection()
            
            assert result is True
            mock_prefect_client.api_healthcheck.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_prefect_connection_failure(self, mock_config):
        """测试Prefect连接检查失败"""
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            with patch("prefect.client.orchestration.get_client") as mock_get_client:
                mock_client = AsyncMock()
                mock_client.api_healthcheck.side_effect = Exception("Connection failed")
                mock_get_client.return_value.__aenter__.return_value = mock_client
                
                result = await manager.check_prefect_connection()
                
                assert result is False
    
    def test_deploy_flow_success(self, mock_config, mock_flow, mock_successful_deployment):
        """测试流程部署成功"""
        mock_config.is_container_env = False
        mock_config.work_pool_name = "test-pool"
        mock_config.deployment_timeout = 30
        
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            # Mock flow.deploy方法
            mock_flow.deploy = mock_successful_deployment
            
            deployment_config = {
                "name": "test-deployment",
                "schedule": {"interval": 3600},
                "tags": ["test"],
                "description": "Test deployment",
            }
            
            result = manager._deploy_flow(mock_flow, deployment_config)
            
            assert result == "deployment-123-success"
    
    def test_deploy_flow_timeout(self, mock_config, mock_flow):
        """测试流程部署超时"""
        mock_config.is_container_env = False
        mock_config.work_pool_name = "test-pool"
        mock_config.deployment_timeout = 1  # 很短的超时时间
        
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            # Mock一个慢速的deploy方法
            def slow_deploy(**kwargs):
                import time
                time.sleep(2)  # 超过超时时间
                return "deployment-id"
            
            mock_flow.deploy = slow_deploy
            
            deployment_config = {"name": "test-deployment"}
            
            with pytest.raises(TimeoutError, match="部署 'test-deployment' 超时"):
                manager._deploy_flow(mock_flow, deployment_config)
    
    def test_deploy_flow_container_env(self, mock_config, mock_flow, mock_successful_deployment):
        """测试容器环境下的流程部署"""
        mock_config.is_container_env = True
        mock_config.work_pool_name = "test-pool"
        mock_config.deployment_timeout = 30
        
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            # 验证deploy被调用时包含build=False, push=False
            def verify_deploy(**kwargs):
                assert kwargs.get("build") is False
                assert kwargs.get("push") is False
                return "deployment-123-success"
            
            mock_flow.deploy = verify_deploy
            
            deployment_config = {"name": "test-deployment"}
            
            result = manager._deploy_flow(mock_flow, deployment_config)
            assert result == "deployment-123-success"
    
    def test_handle_deployment_error_timeout(self, mock_config):
        """测试处理超时错误"""
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            with patch("src.deployment.logger") as mock_logger:
                error = Exception("ConnectTimeoutError occurred")
                manager._handle_deployment_error(error)
                
                # 验证记录了正确的错误信息
                mock_logger.error.assert_called()
                mock_logger.info.assert_called()
    
    def test_handle_deployment_error_work_pool(self, mock_config):
        """测试处理工作池错误"""
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            with patch("src.deployment.logger") as mock_logger:
                error = Exception("work_pool not found")
                manager._handle_deployment_error(error)
                
                # 验证记录了工作池相关的错误信息
                mock_logger.error.assert_called()
                mock_logger.info.assert_called()
    
    def test_deploy_all_success(self, mock_config):
        """测试部署所有流程成功"""
        mock_config.is_container_env = False
        
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            with patch.object(manager, "_deploy_flow") as mock_deploy:
                mock_deploy.return_value = "deployment-123"
                
                results = manager.deploy_all()
                
                # 验证所有流程都被部署
                assert len(results) == 3  # hello, health-check, process-pdf
                
                for flow_name, result in results.items():
                    assert result["status"] == "success"
                    assert result["id"] == "deployment-123"
    
    def test_deploy_all_with_failure_local_env(self, mock_config):
        """测试本地环境下部署失败"""
        mock_config.is_container_env = False
        
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            with patch.object(manager, "_deploy_flow") as mock_deploy:
                mock_deploy.side_effect = Exception("Deployment failed")
                
                # 本地环境下遇到错误应该抛出异常
                with pytest.raises(Exception, match="Deployment failed"):
                    manager.deploy_all()
    
    def test_deploy_all_with_failure_container_env(self, mock_config):
        """测试容器环境下部署失败"""
        mock_config.is_container_env = True
        
        with patch("src.deployment.config", mock_config):
            manager = DeploymentManager()
            
            with patch.object(manager, "_deploy_flow") as mock_deploy:
                mock_deploy.side_effect = Exception("Deployment failed")
                
                # 容器环境下应该继续执行，记录错误但不抛出异常
                results = manager.deploy_all()
                
                # 验证所有流程都记录了失败状态
                for flow_name, result in results.items():
                    assert result["status"] == "failed"
                    assert "Deployment failed" in result["error"]


class TestDeployFlowsFunction:
    """测试deploy_flows函数"""
    
    def test_deploy_flows_function(self, mock_config):
        """测试deploy_flows入口函数"""
        with patch("src.deployment.config", mock_config):
            with patch("src.deployment.DeploymentManager") as mock_manager_class:
                mock_manager = Mock()
                mock_manager.deploy_all.return_value = {"test": "result"}
                mock_manager_class.return_value = mock_manager
                
                from src.deployment import deploy_flows
                
                result = deploy_flows()
                
                # 验证创建了DeploymentManager实例并调用了deploy_all
                mock_manager_class.assert_called_once()
                mock_manager.deploy_all.assert_called_once()
                assert result == {"test": "result"}
