"""Anthropic Claude provider implementation."""

import os
from typing import Any, Dict, List

from anthropic import AsyncAnthropic

from .base import ChatRequest, ChatResponse, LLMProvider


class AnthropicLLMProvider(LLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        api_key = os.getenv(config.get("api_key_env", "ANTHROPIC_API_KEY"))
        self.client = AsyncAnthropic(api_key=api_key) if api_key else None
        self.models = [model["name"] for model in config.get("models", [])]
    
    async def is_available(self) -> bool:
        """Check if Anthropic is available."""
        if not self.client or not self.enabled:
            return False
        
        try:
            # Test with a simple request
            await self.client.messages.create(
                model=self.models[0] if self.models else "claude-3-sonnet-20240229",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception:
            return False
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate chat completion using Claude."""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")
        
        # Convert messages to Anthropic format
        # Anthropic requires system messages to be separate
        system_message = None
        messages = []
        
        for msg in request.messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                messages.append({"role": msg.role, "content": msg.content})
        
        # Use specified model or default to first available
        model = request.model or self.models[0] if self.models else "claude-3-sonnet-20240229"
        
        kwargs = {
            "model": model,
            "max_tokens": request.max_tokens or 4096,
            "messages": messages,
            "temperature": request.temperature,
        }
        
        if system_message:
            kwargs["system"] = system_message
        
        response = await self.client.messages.create(**kwargs)
        
        # Extract content from response
        content = ""
        if response.content:
            content = "".join([
                block.text for block in response.content 
                if hasattr(block, 'text')
            ])
        
        usage = None
        if hasattr(response, 'usage') and response.usage:
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }
        
        return ChatResponse(
            content=content,
            model=model,
            provider=self.name,
            usage=usage,
            finish_reason=response.stop_reason,
        )
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models."""
        return self.models