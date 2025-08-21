"""
配置模块的单元测试
"""
import os
from unittest.mock import patch

import pytest

from config import Config, _get_env_bool


class TestGetEnvBool:
    """测试环境变量布尔值解析函数"""
    
    def test_get_env_bool_true_values(self):
        """测试真值情况"""
        true_values = ["1", "true", "True", "TRUE", "yes", "Yes", "YES", "on", "On", "ON"]
        
        for value in true_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                assert _get_env_bool("TEST_BOOL") is True
    
    def test_get_env_bool_false_values(self):
        """测试假值情况"""
        false_values = ["0", "false", "False", "FALSE", "no", "No", "NO", "off", "Off", "OFF"]
        
        for value in false_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                assert _get_env_bool("TEST_BOOL") is False
    
    def test_get_env_bool_default_value(self):
        """测试默认值"""
        # 环境变量不存在时使用默认值
        with patch.dict(os.environ, {}, clear=True):
            assert _get_env_bool("NONEXISTENT_VAR", default=True) is True
            assert _get_env_bool("NONEXISTENT_VAR", default=False) is False
    
    def test_get_env_bool_empty_string(self):
        """测试空字符串"""
        with patch.dict(os.environ, {"TEST_BOOL": ""}):
            assert _get_env_bool("TEST_BOOL") is False


class TestConfig:
    """测试配置类"""
    
    def test_config_default_values(self):
        """测试默认配置值"""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            assert config.prefect_api_url == "http://172.31.0.55:4200/api"
            assert config.work_pool_name == "my-docker-pool2"
            assert config.image_repo == "ghcr.io/samples28/cicd-example"
            assert config.image_tag is None
            assert config.log_level == "INFO"
            assert config.environment == "development"
            assert config.deploy_mode is False
            assert config.schedule_interval == 3600
            assert config.api_timeout == 300
            assert config.deployment_timeout == 60
    
    def test_config_from_env_vars(self, mock_env_vars):
        """测试从环境变量读取配置"""
        config = Config()
        
        assert config.prefect_api_url == "http://test-api:4200/api"
        assert config.work_pool_name == "test-pool"
        assert config.image_repo == "test/repo"
        assert config.image_tag == "test-tag"
        assert config.log_level == "DEBUG"
        assert config.environment == "test"
        assert config.deploy_mode is False
    
    def test_full_image_name_with_tag(self):
        """测试带标签的完整镜像名称"""
        config = Config()
        config.image_repo = "test/repo"
        config.image_tag = "v1.0.0"
        
        assert config.full_image_name == "test/repo:v1.0.0"
    
    def test_full_image_name_without_tag(self):
        """测试不带标签的完整镜像名称"""
        config = Config()
        config.image_repo = "test/repo"
        config.image_tag = None
        
        assert config.full_image_name == "test/repo"
    
    @patch("os.path.exists")
    def test_is_container_env(self, mock_exists):
        """测试容器环境检测"""
        config = Config()
        
        # 模拟在容器中
        mock_exists.return_value = True
        assert config.is_container_env is True
        
        # 模拟不在容器中
        mock_exists.return_value = False
        assert config.is_container_env is False
    
    def test_is_production(self):
        """测试生产环境检测"""
        config = Config()
        
        config.environment = "production"
        assert config.is_production is True
        
        config.environment = "development"
        assert config.is_production is False
        
        config.environment = "PRODUCTION"
        assert config.is_production is True
    
    def test_validate_required_settings_deploy_mode(self):
        """测试部署模式下的必需配置验证"""
        config = Config()
        config.deploy_mode = True
        
        # 所有必需配置都存在
        config.prefect_api_url = "http://test:4200/api"
        config.work_pool_name = "test-pool"
        config.image_repo = "test/repo"
        config.api_timeout = 300
        config.deployment_timeout = 60
        
        missing = config.validate_required_settings()
        assert missing == []
        
        # 缺少必需配置
        config.prefect_api_url = ""
        config.work_pool_name = ""
        config.image_repo = ""
        
        missing = config.validate_required_settings()
        assert "PREFECT_API_URL" in missing
        assert "WORK_POOL_NAME" in missing
        assert "IMAGE_REPO" in missing
    
    def test_validate_required_settings_non_deploy_mode(self):
        """测试非部署模式下的配置验证"""
        config = Config()
        config.deploy_mode = False
        
        # 非部署模式下不检查Prefect相关配置
        config.prefect_api_url = ""
        config.work_pool_name = ""
        config.image_repo = ""
        
        missing = config.validate_required_settings()
        # 只检查超时配置
        assert len([m for m in missing if "TIMEOUT" in m]) == 0
    
    def test_validate_timeout_settings(self):
        """测试超时配置验证"""
        config = Config()
        
        # 无效的超时值
        config.api_timeout = 0
        config.deployment_timeout = -1
        
        missing = config.validate_required_settings()
        assert any("API_TIMEOUT" in m for m in missing)
        assert any("DEPLOYMENT_TIMEOUT" in m for m in missing)
    
    def test_get_config_summary(self):
        """测试配置摘要"""
        config = Config()
        config.prefect_api_url = "http://test:4200/api"
        config.work_pool_name = "test-pool"
        config.image_repo = "test/repo"
        config.image_tag = "v1.0.0"
        
        summary = config.get_config_summary()
        
        assert summary["prefect_api_url"] == "http://test:4200/api"
        assert summary["work_pool_name"] == "test-pool"
        assert summary["image_repo"] == "test/repo"
        assert summary["image_tag"] == "v1.0.0"
        assert summary["full_image_name"] == "test/repo:v1.0.0"
        assert "environment" in summary
        assert "deploy_mode" in summary
        assert "is_container_env" in summary
        assert "is_production" in summary
    
    @patch("builtins.print")
    def test_print_config_info(self, mock_print):
        """测试配置信息打印"""
        config = Config()
        config.print_config_info()
        
        # 验证print被调用
        assert mock_print.called
        
        # 验证打印的内容包含关键信息
        printed_content = "".join(str(call) for call in mock_print.call_args_list)
        assert "Prefect API URL" in printed_content
        assert "工作池名称" in printed_content
        assert "Docker 镜像" in printed_content
