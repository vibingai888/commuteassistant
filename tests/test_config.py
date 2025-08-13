"""
Unit tests for configuration module
"""

import os
import pytest
from unittest.mock import patch
from app.config import Config


class TestConfig:
    """Test cases for Config class"""
    
    def test_default_values(self):
        """Test default configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.API_HOST == "0.0.0.0"
            assert config.API_PORT == 8080
            assert config.DEBUG is False
            assert config.LOG_LEVEL == "INFO"
            assert config.LOG_FILE == "podcast_api.log"
            assert config.DEFAULT_MINUTES == 3
            assert config.MAX_MINUTES == 15
            assert config.MIN_FIRST_CHUNK_WORDS == 65
            assert config.TARGET_CHUNK_WORDS == 100
    
    def test_environment_variables(self):
        """Test configuration from environment variables"""
        test_env = {
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "LOG_FILE": "test.log",
            "GOOGLE_API_KEY": "test-api-key",
            "GOOGLE_CLOUD_PROJECT": "test-project"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            assert config.API_HOST == "127.0.0.1"
            assert config.API_PORT == 9000
            assert config.DEBUG is True
            assert config.LOG_LEVEL == "DEBUG"
            assert config.LOG_FILE == "test.log"
            assert config.GOOGLE_API_KEY == "test-api-key"
            assert config.GOOGLE_CLOUD_PROJECT == "test-project"
    
    def test_validate_success(self):
        """Test successful validation with required environment variables"""
        test_env = {
            "GOOGLE_API_KEY": "test-api-key",
            "GOOGLE_CLOUD_PROJECT": "test-project"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            # Should not raise any exception
            config.validate()
    
    def test_validate_missing_api_key(self):
        """Test validation failure when API key is missing"""
        test_env = {
            "GOOGLE_CLOUD_PROJECT": "test-project"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            with pytest.raises(ValueError, match="GOOGLE_API_KEY environment variable is required"):
                config.validate()
    
    def test_validate_missing_project(self):
        """Test validation failure when project is missing"""
        test_env = {
            "GOOGLE_API_KEY": "test-api-key"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            with pytest.raises(ValueError, match="GOOGLE_CLOUD_PROJECT environment variable is required"):
                config.validate()
    
    def test_validate_optional_credentials(self):
        """Test that GOOGLE_APPLICATION_CREDENTIALS is optional"""
        test_env = {
            "GOOGLE_API_KEY": "test-api-key",
            "GOOGLE_CLOUD_PROJECT": "test-project"
            # Note: GOOGLE_APPLICATION_CREDENTIALS is not set
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            # Should not raise any exception
            config.validate()
    
    def test_port_conversion(self):
        """Test that API_PORT is properly converted to integer"""
        test_env = {
            "API_PORT": "1234"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            assert config.API_PORT == 1234
            assert isinstance(config.API_PORT, int)
    
    def test_debug_conversion(self):
        """Test that DEBUG is properly converted to boolean"""
        test_env = {
            "DEBUG": "true"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            assert config.DEBUG is True
        
        test_env = {
            "DEBUG": "false"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            assert config.DEBUG is False
