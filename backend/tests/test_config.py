"""
P.R.I.S.M. Config Tests

Tests for the configuration module.
"""

import pytest
from config import get_settings

class TestConfig:
    """Tests for configuration module."""

    def test_config_loading(self):
        """Test configuration loading."""
        settings = get_settings()
        assert settings is not None
        assert settings.model_name is not None
        assert settings.model_backend is not None

    def test_config_values(self):
        """Test that configuration values are loaded correctly."""
        settings = get_settings()
        assert isinstance(settings.model_name, str)
        assert isinstance(settings.model_backend, str)
        assert settings.model_host is not None
        assert settings.model_port is not None