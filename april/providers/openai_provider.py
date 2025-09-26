"""OpenAI provider implementation."""

import os
from typing import Any, Dict, List

import httpx
from openai import AsyncOpenAI

from .base import (
    ChatRequest,
    ChatResponse,
    ImageProvider,
    ImageRequest,
    ImageResponse,
    LLMProvider,
)


class OpenAILLMProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        api_key = os.getenv(config.get("api_key_env", "OPENAI_API_KEY"))
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.models = [model["name"] for model in config.get("models", [])]
    
    async def is_available(self) -> bool:
        """Check if OpenAI is available."""
        if not self.client or not self.enabled:
            return False
        
        try:
            # Test with a simple request
            await self.client.models.list()
            return True
        except Exception:
            return False
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate chat completion using OpenAI."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        # Convert messages to OpenAI format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Use specified model or default to first available
        model = request.model or self.models[0] if self.models else "gpt-3.5-turbo"
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        choice = response.choices[0]
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        return ChatResponse(
            content=choice.message.content or "",
            model=model,
            provider=self.name,
            usage=usage,
            finish_reason=choice.finish_reason,
        )
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models."""
        return self.models


class OpenAIImageProvider(ImageProvider):
    """OpenAI image provider."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        api_key = os.getenv(config.get("api_key_env", "OPENAI_API_KEY"))
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.models = [model["name"] for model in config.get("models", [])]
    
    async def is_available(self) -> bool:
        """Check if OpenAI DALL-E is available."""
        if not self.client or not self.enabled:
            return False
        
        try:
            # Test availability by listing models
            await self.client.models.list()
            return True
        except Exception:
            return False
    
    async def generate(self, request: ImageRequest) -> ImageResponse:
        """Generate image using DALL-E."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        model = request.model or self.models[0] if self.models else "dall-e-3"
        
        response = await self.client.images.generate(
            model=model,
            prompt=request.prompt,
            size=request.size,
            quality="standard",
            n=1,
        )
        
        image = response.data[0]
        
        return ImageResponse(
            url=image.url or "",
            model=model,
            provider=self.name,
            revised_prompt=image.revised_prompt,
        )