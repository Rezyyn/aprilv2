"""Test configuration loading."""

import pytest
import tempfile
import os
from pathlib import Path

from april.config.settings import Settings


def test_load_providers_config():
    """Test loading providers configuration."""
    # Create a temporary config file
    config_content = """
providers:
  llm:
    openai:
      enabled: true
      weight: 0.5
      models:
        - name: "gpt-3.5-turbo"
          max_tokens: 4096
          capabilities: ["text"]
      api_key_env: "OPENAI_API_KEY"
      
logging:
  loki:
    enabled: false
    url: "http://localhost:3100"
    
core:
  memory:
    enabled: true
    backend: "loki"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name
    
    try:
        settings = Settings(providers_config_path=temp_path)
        settings.load_providers_config()
        
        # Test providers configuration
        assert settings.providers is not None
        assert "openai" in settings.providers.llm
        assert settings.providers.llm["openai"].enabled is True
        assert settings.providers.llm["openai"].weight == 0.5
        assert len(settings.providers.llm["openai"].models) == 1
        assert settings.providers.llm["openai"].models[0].name == "gpt-3.5-turbo"
        
        # Test logging configuration
        assert settings.logging is not None
        assert settings.logging.loki["enabled"] is False
        
        # Test core configuration
        assert settings.core is not None
        assert settings.core.memory["enabled"] is True
        
    finally:
        os.unlink(temp_path)


def test_get_enabled_providers():
    """Test getting enabled providers."""
    config_content = """
providers:
  llm:
    openai:
      enabled: true
      weight: 0.5
    claude:
      enabled: false
      weight: 0.3
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name
    
    try:
        settings = Settings(providers_config_path=temp_path)
        settings.load_providers_config()
        
        enabled = settings.get_enabled_providers("llm")
        assert len(enabled) == 1
        assert "openai" in enabled
        assert "claude" not in enabled
        
    finally:
        os.unlink(temp_path)