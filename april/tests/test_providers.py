"""Test provider implementations."""

import pytest
from unittest.mock import AsyncMock, patch

from april.providers.base import ChatRequest, ChatMessage, ImageRequest, SpeechRequest
from april.providers.openai_provider import OpenAILLMProvider, OpenAIImageProvider
from april.providers.deepseek_provider import DeepSeekLLMProvider


@pytest.mark.asyncio
async def test_openai_provider_initialization():
    """Test OpenAI provider initialization."""
    config = {
        "enabled": True,
        "weight": 0.5,
        "models": [{"name": "gpt-3.5-turbo", "max_tokens": 4096, "capabilities": ["text"]}],
        "api_key_env": "OPENAI_API_KEY"
    }
    
    provider = OpenAILLMProvider("openai", config)
    assert provider.name == "openai"
    assert provider.weight == 0.5
    assert provider.enabled is True
    assert len(provider.models) == 1
    assert provider.models[0] == "gpt-3.5-turbo"


@pytest.mark.asyncio
async def test_openai_chat_request():
    """Test OpenAI chat request."""
    config = {
        "enabled": True,
        "weight": 0.5,
        "models": [{"name": "gpt-3.5-turbo", "max_tokens": 4096, "capabilities": ["text"]}],
        "api_key_env": "OPENAI_API_KEY"
    }
    
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        provider = OpenAILLMProvider("openai", config)
        
        # Mock the client
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Hello, how can I help you?"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = AsyncMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 8
        mock_response.usage.total_tokens = 18
        
        with patch.object(provider.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            request = ChatRequest(
                messages=[ChatMessage(role="user", content="Hello")]
            )
            
            response = await provider.chat(request)
            
            assert response.content == "Hello, how can I help you?"
            assert response.provider == "openai"
            assert response.usage["total_tokens"] == 18


@pytest.mark.asyncio
async def test_deepseek_provider_initialization():
    """Test DeepSeek provider initialization."""
    config = {
        "enabled": True,
        "weight": 0.3,
        "models": [{"name": "deepseek-chat", "max_tokens": 4096, "capabilities": ["text", "code"]}],
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1"
    }
    
    provider = DeepSeekLLMProvider("deepseek", config)
    assert provider.name == "deepseek"
    assert provider.weight == 0.3
    assert provider.enabled is True
    assert provider.base_url == "https://api.deepseek.com/v1"


@pytest.mark.asyncio
async def test_provider_availability():
    """Test provider availability check."""
    config = {
        "enabled": True,
        "weight": 0.5,
        "models": [{"name": "gpt-3.5-turbo", "max_tokens": 4096, "capabilities": ["text"]}],
        "api_key_env": "OPENAI_API_KEY"
    }
    
    # Test without API key
    provider = OpenAILLMProvider("openai", config)
    is_available = await provider.is_available()
    assert is_available is False  # No API key configured
    
    # Test with API key but mock unavailable
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        provider = OpenAILLMProvider("openai", config)
        
        with patch.object(provider.client.models, 'list', side_effect=Exception("API Error")):
            is_available = await provider.is_available()
            assert is_available is False