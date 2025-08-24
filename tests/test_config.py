"""
配置模块测试
"""
import pytest
import os
from unittest.mock import patch
from config import Config


class TestConfig:
    """配置类测试"""
    
    def test_default_values(self):
        """测试默认配置值"""
        config = Config()
        
        assert config.prefect_api_url == "http://172.31.0.55:4200/api"
        assert config.work_pool_name == "my-docker-pool2"
        assert config.log_level == "INFO"
        assert config.environment == "development"
        assert config.deploy_mode is False
        assert config.schedule_interval == 3600
        assert config.api_timeout == 300
        assert config.deployment_timeout == 60
    
    def test_environment_variable_override(self):
        """测试环境变量覆盖"""
        with patch.dict(os.environ, {
            'PREFECT_API_URL': 'http://custom-api:4200/api',
            'WORK_POOL_NAME': 'custom-pool',
            'DEPLOY_MODE': 'true',
            'LOG_LEVEL': 'DEBUG',
            'SCHEDULE_INTERVAL': '7200'
        }):
            config = Config()
            
            assert config.prefect_api_url == "http://custom-api:4200/api"
            assert config.work_pool_name == "custom-pool"
            assert config.deploy_mode is True
            assert config.log_level == "DEBUG"
            assert config.schedule_interval == 7200
    
    def test_full_image_name(self):
        """测试完整镜像名称生成"""
        config = Config()
        config.image_repo = "test-repo"
        config.image_tag = "v1.0"
        
        assert config.full_image_name == "test-repo:v1.0"
        
        config.image_tag = None
        assert config.full_image_name == "test-repo"
    
    def test_validate_required_settings_deploy_mode(self):
        """测试部署模式下的配置验证"""
        config = Config()
        config.deploy_mode = True
        config.prefect_api_url = ""
        
        missing = config.validate_required_settings()
        assert "PREFECT_API_URL" in missing
    
    def test_validate_required_settings_timeout(self):
        """测试超时配置验证"""
        config = Config()
        config.api_timeout = 0
        
        missing = config.validate_required_settings()
        assert any("PREFECT_API_TIMEOUT" in item for item in missing)
    
    def test_validate_network_settings(self):
        """测试网络设置验证"""
        config = Config()
        config.deploy_mode = True
        config.prefect_api_url = "http://valid-url:4200/api"
        
        assert config.validate_network_settings() is True
        
        config.prefect_api_url = "invalid-url"
        assert config.validate_network_settings() is False
    
    def test_is_container_env(self):
        """测试容器环境检测"""
        config = Config()
        
        # 默认情况下不在容器中
        assert config.is_container_env is False
        
        # 模拟容器环境
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            assert config.is_container_env is True
    
    def test_is_production(self):
        """测试生产环境检测"""
        config = Config()
        config.environment = "development"
        assert config.is_production is False
        
        config.environment = "production"
        assert config.is_production is True
        
        config.environment = "PRODUCTION"
        assert config.is_production is True
    
    def test_get_config_summary(self):
        """测试配置摘要"""
        config = Config()
        config.image_repo = "test-repo"
        config.image_tag = "v1.0"
        
        summary = config.get_config_summary()
        
        assert isinstance(summary, dict)
        assert "prefect_api_url" in summary
        assert "full_image_name" in summary
        assert summary["full_image_name"] == "test-repo:v1.0"