"""
Unit tests for app/core/config.py module.
"""

import os
from unittest.mock import patch

from app.core.config import Settings, get_settings


class TestSettings:
    """Tests for the Settings class."""

    def test_default_values(self):
        """Test Settings has correct default values."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.APP_NAME == "Card Approval API"
            assert settings.APP_VERSION == "1.0.0"
            assert settings.DEBUG is False
            assert settings.MLFLOW_TRACKING_URI == "http://127.0.0.1:5000"
            assert settings.MODEL_NAME == "card_approval_model"
            assert settings.MODEL_STAGE == "Production"
            assert settings.LOG_LEVEL == "INFO"
            assert settings.LOG_FORMAT == "text"
            assert settings.CORS_ORIGINS == "*"

    def test_settings_from_environment(self):
        """Test Settings loads from environment variables."""
        env_vars = {
            "APP_NAME": "Test API",
            "APP_VERSION": "2.0.0",
            "DEBUG": "true",
            "MLFLOW_TRACKING_URI": "http://mlflow:5000",
            "MODEL_NAME": "test_model",
            "MODEL_STAGE": "Staging",
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "json",
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:8080",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.APP_NAME == "Test API"
            assert settings.APP_VERSION == "2.0.0"
            assert settings.DEBUG is True
            assert settings.MLFLOW_TRACKING_URI == "http://mlflow:5000"
            assert settings.MODEL_NAME == "test_model"
            assert settings.MODEL_STAGE == "Staging"
            assert settings.LOG_LEVEL == "DEBUG"
            assert settings.LOG_FORMAT == "json"
            assert settings.CORS_ORIGINS == "http://localhost:3000,http://localhost:8080"

    def test_case_sensitive_settings(self):
        """Test Settings is case-sensitive."""
        env_vars = {
            "app_name": "lowercase_name",  # Should not be read
            "APP_NAME": "CorrectName",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.APP_NAME == "CorrectName"

    def test_extra_env_vars_ignored(self):
        """Test extra environment variables are ignored."""
        env_vars = {
            "APP_NAME": "Test API",
            "UNKNOWN_SETTING": "should_be_ignored",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()  # Should not raise
            assert not hasattr(settings, "UNKNOWN_SETTING")

    def test_google_credentials_default_empty(self):
        """Test GOOGLE_APPLICATION_CREDENTIALS defaults to empty."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.GOOGLE_APPLICATION_CREDENTIALS == ""


class TestGetSettings:
    """Tests for the get_settings function."""

    def test_get_settings_returns_settings_instance(self):
        """Test get_settings returns a Settings instance."""
        # Clear cache first
        get_settings.cache_clear()

        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_caching(self):
        """Test get_settings is cached (same instance returned)."""
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_cache_clear(self):
        """Test cache can be cleared to get new instance."""
        get_settings.cache_clear()
        settings1 = get_settings()

        get_settings.cache_clear()
        settings2 = get_settings()

        # After cache clear, should get different instance
        # (though values may be same if env hasn't changed)
        assert settings1 is not settings2
