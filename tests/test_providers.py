"""Tests for provider implementations."""

import pytest
from unittest.mock import AsyncMock, patch
from src.providers.base import Capability
from src.providers.openai_provider import OpenAIProvider
from src.providers.deepseek_provider import DeepSeekProvider
from src.providers.elevenlabs_provider import ElevenLabsProvider


@pytest.fixture
def openai_config():
    return {
        "api_key": "test-key",
        "base_url": "https://api.openai.com/v1",
        "capabilities": ["chat", "draw"],
        "models": {
            "chat": [{"name": "gpt-4", "weight": 100}],
            "draw": [{"name": "dall-e-3", "weight": 100}]
        }
    }


@pytest.fixture
def deepseek_config():
    return {
        "api_key": "test-key",
        "base_url": "https://api.deepseek.com/v1",
        "capabilities": ["chat"],
        "models": {
            "chat": [{"name": "deepseek-chat", "weight": 90}]
        }
    }


@pytest.fixture
def elevenlabs_config():
    return {
        "api_key": "test-key",
        "base_url": "https://api.elevenlabs.io/v1",
        "capabilities": ["speak"],
        "models": {
            "speak": [{"name": "eleven_multilingual_v2", "weight": 100}]
        }
    }


def test_openai_provider_initialization(openai_config):
    """Test OpenAI provider initialization."""
    provider = OpenAIProvider(openai_config)
    
    assert provider.name == "openai"
    assert provider.api_key == "test-key"
    assert provider.base_url == "https://api.openai.com/v1"
    assert Capability.CHAT in provider.capabilities
    assert Capability.DRAW in provider.capabilities
    assert provider.supports_capability(Capability.CHAT)
    assert provider.supports_capability(Capability.DRAW)
    assert not provider.supports_capability(Capability.SPEAK)


def test_deepseek_provider_initialization(deepseek_config):
    """Test DeepSeek provider initialization."""
    provider = DeepSeekProvider(deepseek_config)
    
    assert provider.name == "deepseek"
    assert provider.api_key == "test-key"
    assert provider.supports_capability(Capability.CHAT)
    assert not provider.supports_capability(Capability.DRAW)
    assert not provider.supports_capability(Capability.SPEAK)


def test_elevenlabs_provider_initialization(elevenlabs_config):
    """Test ElevenLabs provider initialization."""
    provider = ElevenLabsProvider(elevenlabs_config)
    
    assert provider.name == "elevenlabs"
    assert provider.api_key == "test-key"
    assert provider.supports_capability(Capability.SPEAK)
    assert not provider.supports_capability(Capability.CHAT)
    assert not provider.supports_capability(Capability.DRAW)


@pytest.mark.asyncio
async def test_openai_chat_unsupported_capability():
    """Test OpenAI provider with unsupported capability."""
    config = {
        "api_key": "test-key",
        "base_url": "https://api.openai.com/v1",
        "capabilities": [],  # No capabilities
        "models": {}
    }
    
    provider = OpenAIProvider(config)
    response = await provider.chat([{"role": "user", "content": "hello"}], "gpt-4")
    
    assert not response.success
    assert "Chat capability not supported" in response.error


@pytest.mark.asyncio
async def test_deepseek_draw_unsupported():
    """Test DeepSeek provider draw method (should be unsupported)."""
    config = {
        "api_key": "test-key",
        "base_url": "https://api.deepseek.com/v1",
        "capabilities": ["chat"],
        "models": {}
    }
    
    provider = DeepSeekProvider(config)
    response = await provider.draw("test prompt", "model")
    
    assert not response.success
    assert "Draw capability not supported by DeepSeek provider" in response.error


@pytest.mark.asyncio
async def test_elevenlabs_chat_unsupported():
    """Test ElevenLabs provider chat method (should be unsupported)."""
    config = {
        "api_key": "test-key",
        "base_url": "https://api.elevenlabs.io/v1",
        "capabilities": ["speak"],
        "models": {}
    }
    
    provider = ElevenLabsProvider(config)
    response = await provider.chat([{"role": "user", "content": "hello"}], "model")
    
    assert not response.success
    assert "Chat capability not supported by ElevenLabs provider" in response.error