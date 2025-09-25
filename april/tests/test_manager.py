"""Test April Manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from april.core.manager import AprilManager
from april.config.settings import Settings
from april.providers.base import ChatRequest, ChatMessage, ChatResponse


@pytest.mark.asyncio
async def test_manager_initialization():
    """Test manager initialization."""
    settings = Settings()
    manager = AprilManager(settings)
    
    assert manager.settings == settings
    assert len(manager.llm_providers) == 0
    assert len(manager.image_providers) == 0
    assert len(manager.speech_providers) == 0


@pytest.mark.asyncio
async def test_provider_selection():
    """Test provider selection algorithm."""
    settings = Settings()
    manager = AprilManager(settings)
    
    # Mock providers with different weights
    provider1 = MagicMock()
    provider1.weight = 0.6
    provider1.name = "provider1"
    
    provider2 = MagicMock()
    provider2.weight = 0.4
    provider2.name = "provider2"
    
    providers = {"provider1": provider1, "provider2": provider2}
    
    # Test selection (should work even though it's random)
    selected = manager._select_provider(providers)
    assert selected in [provider1, provider2]
    
    # Test with no providers
    selected = manager._select_provider({})
    assert selected is None


@pytest.mark.asyncio
async def test_user_context_application():
    """Test user context application."""
    settings = Settings()
    manager = AprilManager(settings)
    
    # Set up user persona and memory
    user_id = "test_user"
    manager.set_user_persona(user_id, "friendly assistant")
    manager.user_memories[user_id] = [
        {
            "user_message": "What's 2+2?",
            "assistant_response": "2+2 equals 4.",
            "timestamp": "now"
        }
    ]
    
    # Create a request
    request = ChatRequest(
        messages=[ChatMessage(role="user", content="What about 3+3?")],
        user_id=user_id
    )
    
    # Apply context
    enhanced_request = await manager._apply_user_context(request)
    
    # Check that system message was added/modified
    system_messages = [msg for msg in enhanced_request.messages if msg.role == "system"]
    assert len(system_messages) >= 1
    
    system_content = system_messages[0].content
    assert "friendly assistant" in system_content
    assert "2+2" in system_content  # Memory context should be included


@pytest.mark.asyncio
async def test_memory_storage():
    """Test memory storage functionality."""
    settings = Settings()
    manager = AprilManager(settings)
    
    user_id = "test_user"
    request = ChatRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        user_id=user_id
    )
    response = ChatResponse(
        content="Hi there!",
        model="test-model",
        provider="test-provider"
    )
    
    # Store memory
    await manager._store_memory(user_id, request, response)
    
    # Check that memory was stored
    assert user_id in manager.user_memories
    assert len(manager.user_memories[user_id]) == 1
    
    memory = manager.user_memories[user_id][0]
    assert memory["user_message"] == "Hello"
    assert memory["assistant_response"] == "Hi there!"
    assert memory["provider"] == "test-provider"


def test_persona_management():
    """Test persona management."""
    settings = Settings()
    manager = AprilManager(settings)
    
    user_id = "test_user"
    persona = "helpful coding assistant"
    
    manager.set_user_persona(user_id, persona)
    
    assert manager.user_personas[user_id] == persona