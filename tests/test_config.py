"""Tests for configuration management."""

import os
import tempfile
import pytest
from src.core.config import load_config, Config


def test_load_config_with_env_vars():
    """Test loading configuration with environment variable substitution."""
    config_content = """
providers:
  openai:
    enabled: true
    api_key: ${TEST_API_KEY}
    base_url: ${TEST_BASE_URL:https://default.com}
    capabilities:
      - chat
    models:
      chat:
        - name: gpt-4
          weight: 100
"""
    
    # Set environment variables
    os.environ["TEST_API_KEY"] = "test-key-123"
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            config = load_config(f.name)
            
            assert config.providers["openai"].api_key == "test-key-123"
            assert config.providers["openai"].base_url == "https://default.com"
            assert config.providers["openai"].enabled is True
            assert "chat" in config.providers["openai"].capabilities
    finally:
        os.unlink(f.name)
        if "TEST_API_KEY" in os.environ:
            del os.environ["TEST_API_KEY"]


def test_load_config_missing_required_env():
    """Test that missing required environment variables raise an error."""
    config_content = """
providers:
  openai:
    api_key: ${MISSING_API_KEY}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        with pytest.raises(ValueError, match="Environment variable MISSING_API_KEY is required"):
            load_config(f.name)
    
    os.unlink(f.name)


def test_load_config_empty_file():
    """Test loading configuration from non-existent file returns empty config."""
    config = load_config("non_existent_file.yml")
    assert isinstance(config, Config)
    assert len(config.providers) == 0