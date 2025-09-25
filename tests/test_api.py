"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import app
from src.providers.base import ProviderResponse


client = TestClient(app)


@pytest.fixture
def mock_manager():
    """Mock the manager for testing."""
    with patch('src.main.manager') as mock:
        yield mock


@pytest.fixture
def mock_loki_logger():
    """Mock the loki logger for testing."""
    with patch('src.main.loki_logger') as mock:
        yield mock


def test_health_endpoint():
    """Test the health endpoint."""
    with patch('src.main.manager.get_health') as mock_health:
        mock_health.return_value = {
            "status": "healthy",
            "providers": {"openai": {"enabled": True, "capabilities": ["chat", "draw"]}},
            "capabilities": {"chat": ["openai"], "draw": ["openai"], "speak": []}
        }
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "providers" in data
        assert "capabilities" in data


@pytest.mark.asyncio
async def test_chat_endpoint_success(mock_manager, mock_loki_logger):
    """Test successful chat endpoint."""
    mock_response = ProviderResponse(
        success=True,
        data={"content": "Hello! How can I help you?", "role": "assistant"},
        provider="openai",
        model="gpt-4",
        usage={"prompt_tokens": 10, "completion_tokens": 15}
    )
    
    mock_manager.chat = AsyncMock(return_value=mock_response)
    
    request_data = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = client.post("/chat", json=request_data, headers={"X-User-ID": "test-user"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["provider"] == "openai"
    assert data["model"] == "gpt-4"
    assert "Hello! How can I help you?" in data["data"]["content"]


@pytest.mark.asyncio
async def test_draw_endpoint_success(mock_manager, mock_loki_logger):
    """Test successful draw endpoint."""
    mock_response = ProviderResponse(
        success=True,
        data={"images": ["https://example.com/image1.png"]},
        provider="openai",
        model="dall-e-3"
    )
    
    mock_manager.draw = AsyncMock(return_value=mock_response)
    
    request_data = {
        "prompt": "A beautiful sunset",
        "size": "1024x1024",
        "n": 1
    }
    
    response = client.post("/draw", json=request_data, headers={"X-User-ID": "test-user"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["provider"] == "openai"
    assert data["model"] == "dall-e-3"
    assert len(data["data"]["images"]) == 1


@pytest.mark.asyncio
async def test_speak_endpoint_success(mock_manager, mock_loki_logger):
    """Test successful speak endpoint."""
    mock_response = ProviderResponse(
        success=True,
        data={
            "audio_base64": "base64audiodata",
            "content_type": "audio/mpeg",
            "voice_id": "21m00Tcm4TlvDq8ikWAM"
        },
        provider="elevenlabs",
        model="eleven_multilingual_v2"
    )
    
    mock_manager.speak = AsyncMock(return_value=mock_response)
    
    request_data = {
        "text": "Hello, this is a test.",
        "voice": "21m00Tcm4TlvDq8ikWAM",
        "stability": 0.5
    }
    
    response = client.post("/speak", json=request_data, headers={"X-User-ID": "test-user"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["provider"] == "elevenlabs"
    assert data["model"] == "eleven_multilingual_v2"
    assert "audio_base64" in data["data"]


@pytest.mark.asyncio
async def test_chat_endpoint_failure(mock_manager, mock_loki_logger):
    """Test chat endpoint with provider failure."""
    mock_response = ProviderResponse(
        success=False,
        error="No available providers for chat capability",
        provider="none",
        model="none"
    )
    
    mock_manager.chat = AsyncMock(return_value=mock_response)
    
    request_data = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    
    response = client.post("/chat", json=request_data, headers={"X-User-ID": "test-user"})
    
    assert response.status_code == 200  # API returns 200 but with success=False
    data = response.json()
    assert data["success"] is False
    assert "No available providers" in data["error"]


def test_chat_endpoint_without_user_id(mock_manager, mock_loki_logger):
    """Test chat endpoint without user ID (should generate one)."""
    mock_response = ProviderResponse(
        success=True,
        data={"content": "Hello!", "role": "assistant"},
        provider="openai",
        model="gpt-4"
    )
    
    mock_manager.chat = AsyncMock(return_value=mock_response)
    
    request_data = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    
    response = client.post("/chat", json=request_data)
    
    assert response.status_code == 200
    # The endpoint should handle missing user_id gracefully