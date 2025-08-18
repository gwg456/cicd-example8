"""
Tests for configuration management
"""
import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from src.config.settings import Settings, Environment, LogLevel, get_settings


class TestSettings:
    """Test Settings configuration class"""
    
    def test_default_settings(self):
        """Test default settings initialization"""
        settings = Settings()
        
        assert settings.app_name == "prefect-cicd"
        assert settings.environment == Environment.DEVELOPMENT
        assert settings.debug is False
        assert settings.log_level == LogLevel.INFO
        assert settings.deploy_mode is False
    
    def test_environment_validation(self):
        """Test environment validation"""
        # Valid environments
        for env in ["development", "staging", "production", "testing"]:
            settings = Settings(environment=env)
            assert settings.environment.value == env
        
        # Invalid environment should default to development
        settings = Settings(environment="invalid")
        assert settings.environment == Environment.DEVELOPMENT
    
    def test_prefect_api_url_validation(self):
        """Test Prefect API URL validation"""
        # URL without scheme should be prefixed
        settings = Settings(prefect_api_url="localhost:4200/api")
        assert str(settings.prefect_api_url) == "http://localhost:4200/api"
        
        # URL with scheme should be preserved
        settings = Settings(prefect_api_url="https://api.prefect.io")
        assert str(settings.prefect_api_url) == "https://api.prefect.io"
        
        # Trailing slashes should be removed
        settings = Settings(prefect_api_url="http://localhost:4200/api/")
        assert str(settings.prefect_api_url) == "http://localhost:4200/api"
    
    def test_jwt_secret_validation(self):
        """Test JWT secret validation in production"""
        # Production with auth enabled requires JWT secret
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment=Environment.PRODUCTION,
                enable_auth=True,
                jwt_secret_key=None
            )
        assert "JWT_SECRET_KEY must be set" in str(exc_info.value)
        
        # Production with auth disabled doesn't require JWT secret
        settings = Settings(
            environment=Environment.PRODUCTION,
            enable_auth=False,
            jwt_secret_key=None
        )
        assert settings.jwt_secret_key is None
    
    def test_timeout_validation(self):
        """Test timeout configuration validation"""
        # Valid timeouts
        settings = Settings(
            api_timeout=30,
            deployment_timeout=60,
            task_timeout=300
        )
        assert settings.api_timeout == 30
        assert settings.deployment_timeout == 60
        assert settings.task_timeout == 300
        
        # Invalid timeouts should raise validation error
        with pytest.raises(ValidationError):
            Settings(api_timeout=-1)
        
        with pytest.raises(ValidationError):
            Settings(deployment_timeout=1000)
    
    def test_schedule_interval_validation(self):
        """Test schedule interval validation"""
        # Valid intervals
        settings = Settings(schedule_interval=3600)
        assert settings.schedule_interval == 3600
        
        # Too short interval
        with pytest.raises(ValidationError):
            Settings(schedule_interval=30)
        
        # Too long interval
        with pytest.raises(ValidationError):
            Settings(schedule_interval=100000)
    
    def test_is_production_property(self):
        """Test is_production property"""
        settings = Settings(environment=Environment.PRODUCTION)
        assert settings.is_production is True
        
        settings = Settings(environment=Environment.DEVELOPMENT)
        assert settings.is_production is False
    
    def test_is_development_property(self):
        """Test is_development property"""
        settings = Settings(environment=Environment.DEVELOPMENT)
        assert settings.is_development is True
        
        settings = Settings(environment=Environment.PRODUCTION)
        assert settings.is_development is False
    
    def test_is_container_env_property(self):
        """Test container environment detection"""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            settings = Settings()
            assert settings.is_container_env is True
            
            mock_exists.return_value = False
            with patch.dict(os.environ, {"CONTAINER_ENV": "true"}):
                settings = Settings()
                assert settings.is_container_env is True
    
    def test_full_image_name_property(self):
        """Test full image name generation"""
        settings = Settings(
            image_repo="test-repo",
            image_tag="v1.0.0"
        )
        assert settings.full_image_name == "test-repo:v1.0.0"
        
        settings = Settings(
            image_repo="test-repo",
            image_tag=None
        )
        assert settings.full_image_name == "test-repo:latest"
    
    def test_get_prefect_settings(self):
        """Test Prefect settings extraction"""
        settings = Settings(
            prefect_api_url="http://localhost:4200/api",
            prefect_api_key="secret-key",
            log_level=LogLevel.DEBUG
        )
        
        prefect_settings = settings.get_prefect_settings()
        
        assert prefect_settings["PREFECT_API_URL"] == "http://localhost:4200/api"
        assert prefect_settings["PREFECT_API_KEY"] == "secret-key"
        assert prefect_settings["PREFECT_LOGGING_LEVEL"] == "DEBUG"
    
    def test_get_docker_job_variables(self):
        """Test Docker job variables generation"""
        settings = Settings(
            log_level=LogLevel.INFO,
            environment=Environment.PRODUCTION
        )
        
        # Container environment
        with patch.object(settings, "is_container_env", True):
            job_vars = settings.get_docker_job_variables()
            assert "env" in job_vars
            assert job_vars["env"]["LOG_LEVEL"] == "INFO"
            assert job_vars["env"]["ENVIRONMENT"] == "production"
        
        # Non-container environment
        with patch.object(settings, "is_container_env", False):
            job_vars = settings.get_docker_job_variables()
            assert "env.LOG_LEVEL" in job_vars
            assert "env.DOCKER_CLIENT_TIMEOUT" in job_vars
    
    def test_validate_deployment_requirements(self):
        """Test deployment requirements validation"""
        # Valid deployment configuration
        settings = Settings(
            deploy_mode=True,
            prefect_api_url="http://localhost:4200/api",
            work_pool_name="test-pool",
            image_repo="test-repo"
        )
        issues = settings.validate_deployment_requirements()
        assert len(issues) == 0
        
        # Missing required settings
        settings = Settings(
            deploy_mode=True,
            prefect_api_url=None,
            work_pool_name="",
            image_repo=""
        )
        issues = settings.validate_deployment_requirements()
        assert "PREFECT_API_URL is required" in issues
        assert "WORK_POOL_NAME is required" in issues
        assert "IMAGE_REPO is required" in issues
        
        # Production requires API key
        settings = Settings(
            deploy_mode=True,
            environment=Environment.PRODUCTION,
            prefect_api_url="http://localhost:4200/api",
            work_pool_name="test-pool",
            image_repo="test-repo",
            prefect_api_key=None
        )
        issues = settings.validate_deployment_requirements()
        assert "PREFECT_API_KEY is required in production" in issues
    
    def test_env_file_loading(self, tmp_path):
        """Test loading settings from .env file"""
        env_file = tmp_path / ".env"
        env_file.write_text("""
APP_NAME=test-app
ENVIRONMENT=staging
LOG_LEVEL=DEBUG
PREFECT_API_URL=http://test:4200/api
        """)
        
        with patch.dict(os.environ, {"ENV_FILE": str(env_file)}):
            settings = Settings(_env_file=str(env_file))
            
            assert settings.app_name == "test-app"
            assert settings.environment == Environment.STAGING
            assert settings.log_level == LogLevel.DEBUG
            assert str(settings.prefect_api_url) == "http://test:4200/api"


class TestGetSettings:
    """Test get_settings function"""
    
    def test_settings_caching(self):
        """Test that settings are cached"""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_settings_cache_clear(self):
        """Test clearing settings cache"""
        settings1 = get_settings()
        
        # Clear cache
        get_settings.cache_clear()
        
        settings2 = get_settings()
        assert settings1 is not settings2


class TestLegacyConfig:
    """Test legacy configuration compatibility"""
    
    def test_legacy_config_import(self):
        """Test that legacy config module can be imported"""
        from config import config
        
        assert hasattr(config, "prefect_api_url")
        assert hasattr(config, "work_pool_name")
        assert hasattr(config, "apply_prefect_settings")
        assert hasattr(config, "validate_required_settings")
    
    def test_legacy_config_compatibility(self):
        """Test legacy config compatibility with new settings"""
        from config import config
        
        # Should use values from new settings system
        assert config.prefect_api_url is not None
        assert config.work_pool_name is not None
        assert config.deploy_mode is not None