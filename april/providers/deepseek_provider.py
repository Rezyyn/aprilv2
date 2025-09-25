"""DeepSeek provider implementation."""

import os
from typing import Any, Dict, List

import httpx

from .base import (
    ChatRequest,
    ChatResponse,
    ImageProvider,
    ImageRequest,
    ImageResponse,
    LLMProvider,
)


class DeepSeekLLMProvider(LLMProvider):
    """DeepSeek LLM provider."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv(config.get("api_key_env", "DEEPSEEK_API_KEY"))
        self.base_url = config.get("base_url", "https://api.deepseek.com/v1")
        self.models = [model["name"] for model in config.get("models", [])]
    
    async def is_available(self) -> bool:
        """Check if DeepSeek is available."""
        if not self.api_key or not self.enabled:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate chat completion using DeepSeek."""
        if not self.api_key:
            raise RuntimeError("DeepSeek API key not configured")
        
        # Convert messages to OpenAI-compatible format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        model = request.model or self.models[0] if self.models else "deepseek-chat"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                }
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"DeepSeek API error: {response.status_code}")
            
            data = response.json()
            choice = data["choices"][0]
            
            usage = None
            if "usage" in data:
                usage = {
                    "prompt_tokens": data["usage"]["prompt_tokens"],
                    "completion_tokens": data["usage"]["completion_tokens"],
                    "total_tokens": data["usage"]["total_tokens"],
                }
            
            return ChatResponse(
                content=choice["message"]["content"],
                model=model,
                provider=self.name,
                usage=usage,
                finish_reason=choice.get("finish_reason"),
            )
    
    def get_available_models(self) -> List[str]:
        """Get available DeepSeek models."""
        return self.models


class DeepSeekImageProvider(ImageProvider):
    """DeepSeek image provider (placeholder implementation)."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv(config.get("api_key_env", "DEEPSEEK_API_KEY"))
        self.models = [model["name"] for model in config.get("models", [])]
    
    async def is_available(self) -> bool:
        """Check if DeepSeek image generation is available."""
        # Placeholder - DeepSeek doesn't have image generation yet
        return False
    
    async def generate(self, request: ImageRequest) -> ImageResponse:
        """Generate image using DeepSeek (placeholder)."""
        raise NotImplementedError("DeepSeek image generation not yet available")