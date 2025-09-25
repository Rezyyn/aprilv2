"""Base provider interface for April Core service."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel


class Capability(Enum):
    """Supported capabilities."""
    CHAT = "chat"
    DRAW = "draw"
    SPEAK = "speak"


class ProviderResponse(BaseModel):
    """Standard response from providers."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """Base class for all providers."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize provider with configuration."""
        self.name = name
        self.config = config
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.capabilities = [Capability(cap) for cap in config.get("capabilities", [])]
        
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> ProviderResponse:
        """Handle chat completion."""
        pass
        
    @abstractmethod
    async def draw(self, prompt: str, model: str, **kwargs) -> ProviderResponse:
        """Handle image generation."""
        pass
        
    @abstractmethod
    async def speak(self, text: str, model: str, voice: str = None, **kwargs) -> ProviderResponse:
        """Handle text-to-speech."""
        pass
        
    def supports_capability(self, capability: Capability) -> bool:
        """Check if provider supports a specific capability."""
        return capability in self.capabilities
        
    def get_models_for_capability(self, capability: Capability) -> List[Dict[str, Any]]:
        """Get available models for a capability."""
        cap_name = capability.value
        return self.config.get("models", {}).get(cap_name, [])