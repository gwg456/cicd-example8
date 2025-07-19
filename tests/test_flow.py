"""
工作流测试模块
测试 flow.py 中的主要功能
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
import sys
import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flow import hello, deploy_flow, _deploy_in_container, _deploy_locally
from config import Config

class TestHelloFlow:
    """测试 hello 工作流"""
    
    def test_hello_flow_runs_successfully(self):
        """测试 hello 工作流能够正常运行"""
        # 这个测试会实际运行工作流，可能需要较长时间
        # 在生产环境中可能需要 mock time.sleep
        with patch('time.sleep') as mock_sleep:
            result = hello()
            assert result is None
            mock_sleep.assert_called_once_with(20)

class TestDeployFlow:
    """测试部署功能"""
    
    @patch('os.environ.get')
    def test_deploy_flow_with_image_tag(self, mock_env_get):
        """测试使用环境变量中的镜像标签进行部署"""
        mock_env_get.side_effect = lambda key, default=None: {
            'IMAGE_REPO': 'test-repo',
            'IMAGE_TAG': 'v1.0.0',
            'WORK_POOL_NAME': 'test-pool',
            'DEPLOY_MODE': 'true'
        }.get(key, default)
        
        with patch('os.path.exists', return_value=True):
            with patch('flow._deploy_in_container') as mock_deploy:
                deploy_flow()
                mock_deploy.assert_called_once_with('test-repo:v1.0.0')
    
    @patch('os.environ.get')
    @patch('datetime.datetime.now')
    def test_deploy_flow_without_image_tag(self, mock_datetime, mock_env_get):
        """测试没有镜像标签时自动生成标签"""
        mock_datetime.return_value = datetime.datetime(2025, 1, 1, 12, 0)
        mock_env_get.side_effect = lambda key, default=None: {
            'IMAGE_REPO': 'test-repo',
            'WORK_POOL_NAME': 'test-pool',
            'DEPLOY_MODE': 'true'
        }.get(key, default)
        
        with patch('os.path.exists', return_value=True):
            with patch('flow._deploy_in_container') as mock_deploy:
                deploy_flow()
                mock_deploy.assert_called_once_with('test-repo:v202501011200')

class TestDeployInContainer:
    """测试容器内部署功能"""
    
    @patch('prefect_docker.containers.DockerContainer')
    def test_deploy_with_docker_container(self, mock_docker_container):
        """测试使用 DockerContainer 进行部署"""
        mock_infrastructure = MagicMock()
        mock_docker_container.return_value = mock_infrastructure
        
        with patch('flow.hello.deploy') as mock_deploy:
            mock_deploy.return_value = "deployment-123"
            
            with patch('signal.signal'), patch('signal.alarm'):
                _deploy_in_container('test-image:latest')
                
                mock_deploy.assert_called_once()
                call_args = mock_deploy.call_args
                assert call_args[1]['name'] == 'prod-deployment'
                assert call_args[1]['work_pool_name'] == 'my-docker-pool2'
                assert call_args[1]['infrastructure'] == mock_infrastructure
    
    @patch('prefect_docker.containers.DockerContainer', side_effect=ImportError)
    def test_deploy_without_docker_container(self, mock_docker_container):
        """测试没有 DockerContainer 时的部署"""
        with patch('flow._deploy_with_basic_config') as mock_basic_deploy:
            with patch('signal.signal'), patch('signal.alarm'):
                _deploy_in_container('test-image:latest')
                mock_basic_deploy.assert_called_once_with('test-image:latest')

class TestDeployLocally:
    """测试本地部署功能"""
    
    @patch('tempfile.mkdtemp')
    @patch('flow.hello.deploy')
    def test_deploy_locally(self, mock_deploy, mock_mkdtemp):
        """测试本地部署功能"""
        mock_mkdtemp.return_value = '/tmp/test_logs'
        
        _deploy_locally('test-image:latest')
        
        mock_deploy.assert_called_once()
        call_args = mock_deploy.call_args
        assert call_args[1]['name'] == 'prod-deployment'
        assert call_args[1]['work_pool_name'] == 'my-docker-pool2'
        assert call_args[1]['image'] == 'test-image:latest'

class TestConfig:
    """测试配置功能"""
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试有效配置
        with patch('os.environ.get', return_value='test-value'):
            assert Config.validate_config() is True
        
        # 测试无效配置
        with patch('os.environ.get', return_value=''):
            assert Config.validate_config() is False
    
    def test_get_environment_vars(self):
        """测试环境变量获取"""
        env_vars = Config.get_environment_vars()
        assert 'LOG_LEVEL' in env_vars
        assert 'ENVIRONMENT' in env_vars
        assert 'PYTHONUNBUFFERED' in env_vars
    
    def test_get_deployment_tags(self):
        """测试部署标签获取"""
        tags = Config.get_deployment_tags()
        assert 'production' in tags
        assert 'automated' in tags

if __name__ == '__main__':
    pytest.main([__file__])