"""
Tests for deployment management
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from src.deployment import DeploymentManager, deploy_flows, deploy_flows_async
from src.core import DeploymentError, AppConnectionError, AppTimeoutError, ConfigurationError


class TestDeploymentManager:
    """Test DeploymentManager class"""
    
    @pytest.mark.asyncio
    async def test_check_prefect_connection_success(self, deployment_manager, mock_prefect_client):
        """Test successful Prefect API connection"""
        result = await deployment_manager.check_prefect_connection()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_prefect_connection_timeout(self, deployment_manager):
        """Test Prefect API connection timeout"""
        with patch("prefect.client.orchestration.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.api_healthcheck.side_effect = asyncio.TimeoutError()
            
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_client
            mock_get_client.return_value = mock_context
            
            with pytest.raises(AppTimeoutError) as exc_info:
                await deployment_manager.check_prefect_connection()
            
            assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_check_prefect_connection_error(self, deployment_manager):
        """Test Prefect API connection error"""
        with patch("prefect.client.orchestration.get_client") as mock_get_client:
            mock_get_client.side_effect = Exception("Connection failed")
            
            with pytest.raises(AppConnectionError) as exc_info:
                await deployment_manager.check_prefect_connection()
            
            assert "Connection failed" in str(exc_info.value)
    
    def test_generate_image_tag_with_tag(self, deployment_manager):
        """Test image tag generation with provided tag"""
        deployment_manager.settings.image_tag = "v1.0.0"
        deployment_manager.settings.image_repo = "test-repo"
        
        tag = deployment_manager._generate_image_tag()
        assert tag == "test-repo:v1.0.0"
    
    def test_generate_image_tag_without_tag(self, deployment_manager):
        """Test image tag generation without provided tag"""
        deployment_manager.settings.image_tag = None
        deployment_manager.settings.image_repo = "test-repo"
        
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "202401011200"
            tag = deployment_manager._generate_image_tag()
            assert tag == "test-repo:v202401011200"
    
    @pytest.mark.asyncio
    async def test_validate_work_pool_exists(self, deployment_manager):
        """Test work pool validation when pool exists"""
        mock_client = AsyncMock()
        mock_pool = Mock(name="test-pool")
        mock_client.read_work_pools.return_value = [mock_pool]
        
        result = await deployment_manager._validate_work_pool(mock_client, "test-pool")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_work_pool_not_exists(self, deployment_manager):
        """Test work pool validation when pool doesn't exist"""
        mock_client = AsyncMock()
        mock_pool = Mock(name="other-pool")
        mock_client.read_work_pools.return_value = [mock_pool]
        
        with pytest.raises(DeploymentError) as exc_info:
            await deployment_manager._validate_work_pool(mock_client, "test-pool")
        
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_deploy_flow_success(self, deployment_manager, mock_prefect_client):
        """Test successful flow deployment"""
        mock_flow = Mock()
        mock_flow.deploy.return_value = "deployment-123"
        
        with patch.object(deployment_manager, "check_prefect_connection", return_value=True):
            with patch.object(deployment_manager, "_validate_work_pool", return_value=True):
                result = await deployment_manager.deploy_flow(
                    flow=mock_flow,
                    name="test-flow",
                    tags=["test"],
                    description="Test flow"
                )
        
        assert result == "deployment-123"
        mock_flow.deploy.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deploy_flow_configuration_error(self, deployment_manager):
        """Test flow deployment with configuration error"""
        deployment_manager.settings.prefect_api_url = None
        mock_flow = Mock()
        
        with pytest.raises(ConfigurationError) as exc_info:
            await deployment_manager.deploy_flow(
                flow=mock_flow,
                name="test-flow"
            )
        
        assert "Invalid deployment configuration" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_deploy_flow_connection_error(self, deployment_manager):
        """Test flow deployment with connection error"""
        mock_flow = Mock()
        
        with patch.object(deployment_manager, "check_prefect_connection", return_value=False):
            with pytest.raises(AppConnectionError) as exc_info:
                await deployment_manager.deploy_flow(
                    flow=mock_flow,
                    name="test-flow"
                )
        
        assert "Cannot establish connection" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_deploy_flow_timeout(self, deployment_manager, mock_prefect_client):
        """Test flow deployment timeout"""
        mock_flow = Mock()
        mock_flow.deploy.side_effect = asyncio.TimeoutError()
        
        with patch.object(deployment_manager, "check_prefect_connection", return_value=True):
            with patch.object(deployment_manager, "_validate_work_pool", return_value=True):
                with pytest.raises(DeploymentError) as exc_info:
                    await deployment_manager.deploy_flow(
                        flow=mock_flow,
                        name="test-flow"
                    )
        
        assert "Failed to deploy" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_deploy_all_success(self, deployment_manager):
        """Test deploying all flows successfully"""
        with patch.object(deployment_manager, "deploy_hello_flow", return_value="hello-123"):
            with patch.object(deployment_manager, "deploy_health_check_flow", return_value="health-123"):
                result = await deployment_manager.deploy_all()
        
        assert result["success"] is True
        assert result["deployments"]["hello_flow"] == "hello-123"
        assert result["deployments"]["health_check_flow"] == "health-123"
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_deploy_all_partial_failure(self, deployment_manager):
        """Test partial failure in deploying flows"""
        with patch.object(deployment_manager, "deploy_hello_flow", return_value="hello-123"):
            with patch.object(deployment_manager, "deploy_health_check_flow", side_effect=Exception("Deploy failed")):
                result = await deployment_manager.deploy_all()
        
        assert result["success"] is False
        assert result["deployments"]["hello_flow"] == "hello-123"
        assert len(result["errors"]) == 1
        assert "Deploy failed" in result["errors"][0]["error"]
    
    @pytest.mark.asyncio
    async def test_deploy_all_container_env_error_handling(self, deployment_manager):
        """Test error handling in container environment"""
        deployment_manager.settings.is_container_env = True
        
        with patch.object(deployment_manager, "deploy_hello_flow", side_effect=Exception("Critical error")):
            with patch.object(deployment_manager, "deploy_health_check_flow", side_effect=Exception("Critical error")):
                result = await deployment_manager.deploy_all()
        
        # Should return error info instead of raising
        assert result["success"] is False
        assert len(result["errors"]) == 2


class TestDeploymentFunctions:
    """Test deployment functions"""
    
    @pytest.mark.asyncio
    async def test_deploy_flows_async(self):
        """Test async deploy_flows function"""
        with patch("src.deployment.DeploymentManager") as MockManager:
            mock_instance = MockManager.return_value
            mock_instance.deploy_all = AsyncMock(return_value={"success": True})
            
            result = await deploy_flows_async()
            
            assert result["success"] is True
            mock_instance.deploy_all.assert_called_once()
    
    def test_deploy_flows_sync(self):
        """Test synchronous deploy_flows function"""
        with patch("src.deployment.asyncio.run") as mock_run:
            mock_run.return_value = {"success": True}
            
            result = deploy_flows()
            
            assert result["success"] is True
            mock_run.assert_called_once()
    
    def test_deploy_flows_sync_error(self):
        """Test synchronous deploy_flows with error"""
        with patch("src.deployment.asyncio.run") as mock_run:
            mock_run.side_effect = Exception("Deployment error")
            
            result = deploy_flows()
            
            assert result["success"] is False
            assert "Deployment error" in result["error"]


class TestDeploymentErrorHandling:
    """Test deployment error handling and logging"""
    
    def test_log_deployment_error_timeout(self, deployment_manager, capture_logs):
        """Test error logging for timeout errors"""
        error = Exception("Connection timeout")
        deployment_manager._log_deployment_error(error, "test-flow")
        
        logs = capture_logs.getvalue()
        assert "timeout" in logs.lower()
        assert "Troubleshooting tips" in logs
    
    def test_log_deployment_error_work_pool(self, deployment_manager, capture_logs):
        """Test error logging for work pool errors"""
        error = Exception("Work pool 'test-pool' not found")
        deployment_manager._log_deployment_error(error, "test-flow")
        
        logs = capture_logs.getvalue()
        assert "work pool" in logs.lower()
        assert "prefect work-pool ls" in logs
    
    def test_log_deployment_error_auth(self, deployment_manager, capture_logs):
        """Test error logging for authentication errors"""
        error = Exception("Unauthorized access")
        deployment_manager._log_deployment_error(error, "test-flow")
        
        logs = capture_logs.getvalue()
        assert "authentication" in logs.lower()
        assert "PREFECT_API_KEY" in logs
    
    def test_log_deployment_error_docker(self, deployment_manager, capture_logs):
        """Test error logging for Docker errors"""
        error = Exception("Docker daemon not running")
        deployment_manager._log_deployment_error(error, "test-flow")
        
        logs = capture_logs.getvalue()
        assert "docker" in logs.lower()
        assert "Docker daemon" in logs