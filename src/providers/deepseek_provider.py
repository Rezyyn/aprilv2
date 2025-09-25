"""DeepSeek provider implementation."""

import httpx
from typing import Dict, Any, List
from .base import BaseProvider, ProviderResponse, Capability


class DeepSeekProvider(BaseProvider):
    """DeepSeek provider for chat completion."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("deepseek", config)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0
        )
    
    async def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> ProviderResponse:
        """Handle chat completion using DeepSeek API."""
        if not self.supports_capability(Capability.CHAT):
            return ProviderResponse(
                success=False,
                error="Chat capability not supported",
                provider=self.name,
                model=model
            )
        
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": False
            }
            
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return ProviderResponse(
                success=True,
                data={
                    "content": data["choices"][0]["message"]["content"],
                    "role": data["choices"][0]["message"]["role"]
                },
                provider=self.name,
                model=model,
                usage=data.get("usage")
            )
            
        except Exception as e:
            return ProviderResponse(
                success=False,
                error=str(e),
                provider=self.name,
                model=model
            )
    
    async def draw(self, prompt: str, model: str, **kwargs) -> ProviderResponse:
        """DeepSeek doesn't support image generation."""
        return ProviderResponse(
            success=False,
            error="Draw capability not supported by DeepSeek provider",
            provider=self.name,
            model=model
        )
    
    async def speak(self, text: str, model: str, voice: str = None, **kwargs) -> ProviderResponse:
        """DeepSeek doesn't support TTS."""
        return ProviderResponse(
            success=False,
            error="Speak capability not supported by DeepSeek provider",
            provider=self.name,
            model=model
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()