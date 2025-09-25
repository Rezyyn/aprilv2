"""Base provider interface for April v2."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[ChatMessage]
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


class ImageRequest(BaseModel):
    """Image generation request model."""
    prompt: str
    size: str = "1024x1024"
    model: Optional[str] = None
    user_id: Optional[str] = None


class ImageResponse(BaseModel):
    """Image generation response model."""
    url: str
    model: str
    provider: str
    revised_prompt: Optional[str] = None


class SpeechRequest(BaseModel):
    """Speech generation request model."""
    text: str
    voice: Optional[str] = None
    model: Optional[str] = None
    user_id: Optional[str] = None


class SpeechResponse(BaseModel):
    """Speech generation response model."""
    audio_url: str
    provider: str
    voice: str


class BaseProvider(ABC):
    """Base provider interface."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.weight = config.get("weight", 0.0)
        self.enabled = config.get("enabled", False)
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass


class LLMProvider(BaseProvider):
    """Base LLM provider interface."""
    
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate chat completion."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        pass


class ImageProvider(BaseProvider):
    """Base image provider interface."""
    
    @abstractmethod
    async def generate(self, request: ImageRequest) -> ImageResponse:
        """Generate image."""
        pass


class SpeechProvider(BaseProvider):
    """Base speech provider interface."""
    
    @abstractmethod
    async def synthesize(self, request: SpeechRequest) -> SpeechResponse:
        """Synthesize speech."""
        pass


class VideoProvider(BaseProvider):
    """Base video provider interface."""
    
    @abstractmethod
    async def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate video."""
        pass