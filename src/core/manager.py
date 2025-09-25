"""Core manager for orchestrating providers with capability-based routing and weighting."""

import random
from typing import Dict, List, Optional, Any
from .config import get_config
from .logging import loki_logger
from ..providers.base import BaseProvider, Capability, ProviderResponse
from ..providers.openai_provider import OpenAIProvider
from ..providers.deepseek_provider import DeepSeekProvider
from ..providers.elevenlabs_provider import ElevenLabsProvider


class ProviderManager:
    """Manages all providers and handles routing based on capabilities and weights."""
    
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all enabled providers from configuration."""
        config = get_config()
        for provider_name, provider_config in config.providers.items():
            if not provider_config.enabled:
                continue
                
            try:
                if provider_name == "openai":
                    provider = OpenAIProvider(provider_config.model_dump())
                elif provider_name == "deepseek":
                    provider = DeepSeekProvider(provider_config.model_dump())
                elif provider_name == "elevenlabs":
                    provider = ElevenLabsProvider(provider_config.model_dump())
                else:
                    print(f"Unknown provider: {provider_name}")
                    continue
                
                self.providers[provider_name] = provider
                print(f"Initialized provider: {provider_name}")
                
            except Exception as e:
                print(f"Failed to initialize provider {provider_name}: {e}")
    
    def _get_providers_for_capability(self, capability: Capability) -> List[BaseProvider]:
        """Get all providers that support a specific capability."""
        return [
            provider for provider in self.providers.values()
            if provider.supports_capability(capability)
        ]
    
    def _select_model_by_weight(self, provider: BaseProvider, capability: Capability) -> Optional[str]:
        """Select a model from provider based on weighted random selection."""
        models = provider.get_models_for_capability(capability)
        if not models:
            return None
        
        # Create weighted list
        weighted_models = []
        for model_config in models:
            model_name = model_config.name if hasattr(model_config, 'name') else model_config.get('name')
            weight = model_config.weight if hasattr(model_config, 'weight') else model_config.get('weight', 100)
            weighted_models.extend([model_name] * weight)
        
        return random.choice(weighted_models) if weighted_models else None
    
    def _select_provider_and_model(self, capability: Capability) -> tuple[Optional[BaseProvider], Optional[str]]:
        """Select the best provider and model for a capability using weighted selection."""
        available_providers = self._get_providers_for_capability(capability)
        if not available_providers:
            return None, None
        
        # For now, use simple random selection among available providers
        # In the future, this could be enhanced with more sophisticated routing logic
        provider = random.choice(available_providers)
        model = self._select_model_by_weight(provider, capability)
        
        return provider, model
    
    async def chat(self, messages: List[Dict[str, str]], user_id: str, **kwargs) -> ProviderResponse:
        """Handle chat completion with provider selection and logging."""
        provider, model = self._select_provider_and_model(Capability.CHAT)
        
        if not provider or not model:
            error_msg = "No available providers for chat capability"
            await loki_logger.log_error(user_id, "/chat", error_msg)
            return ProviderResponse(
                success=False,
                error=error_msg,
                provider="none",
                model="none"
            )
        
        import time
        start_time = time.time()
        
        try:
            response = await provider.chat(messages, model, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the interaction
            await loki_logger.log_user_interaction(
                user_id=user_id,
                endpoint="/chat",
                request_data={"messages": messages, "kwargs": kwargs},
                response_data=response.model_dump(),
                provider=provider.name,
                model=model,
                duration_ms=duration_ms
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Chat request failed: {str(e)}"
            await loki_logger.log_error(user_id, "/chat", error_msg, {"provider": provider.name, "model": model})
            return ProviderResponse(
                success=False,
                error=error_msg,
                provider=provider.name,
                model=model
            )
    
    async def draw(self, prompt: str, user_id: str, **kwargs) -> ProviderResponse:
        """Handle image generation with provider selection and logging."""
        provider, model = self._select_provider_and_model(Capability.DRAW)
        
        if not provider or not model:
            error_msg = "No available providers for draw capability"
            await loki_logger.log_error(user_id, "/draw", error_msg)
            return ProviderResponse(
                success=False,
                error=error_msg,
                provider="none",
                model="none"
            )
        
        import time
        start_time = time.time()
        
        try:
            response = await provider.draw(prompt, model, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the interaction
            await loki_logger.log_user_interaction(
                user_id=user_id,
                endpoint="/draw",
                request_data={"prompt": prompt, "kwargs": kwargs},
                response_data=response.model_dump(),
                provider=provider.name,
                model=model,
                duration_ms=duration_ms
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Draw request failed: {str(e)}"
            await loki_logger.log_error(user_id, "/draw", error_msg, {"provider": provider.name, "model": model})
            return ProviderResponse(
                success=False,
                error=error_msg,
                provider=provider.name,
                model=model
            )
    
    async def speak(self, text: str, user_id: str, voice: str = None, **kwargs) -> ProviderResponse:
        """Handle text-to-speech with provider selection and logging."""
        provider, model = self._select_provider_and_model(Capability.SPEAK)
        
        if not provider or not model:
            error_msg = "No available providers for speak capability"
            await loki_logger.log_error(user_id, "/speak", error_msg)
            return ProviderResponse(
                success=False,
                error=error_msg,
                provider="none",
                model="none"
            )
        
        import time
        start_time = time.time()
        
        try:
            response = await provider.speak(text, model, voice=voice, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the interaction
            await loki_logger.log_user_interaction(
                user_id=user_id,
                endpoint="/speak",
                request_data={"text": text, "voice": voice, "kwargs": kwargs},
                response_data=response.model_dump(),
                provider=provider.name,
                model=model,
                duration_ms=duration_ms
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Speak request failed: {str(e)}"
            await loki_logger.log_error(user_id, "/speak", error_msg, {"provider": provider.name, "model": model})
            return ProviderResponse(
                success=False,
                error=error_msg,
                provider=provider.name,
                model=model
            )
    
    async def get_health(self) -> Dict[str, Any]:
        """Get health status of all providers."""
        health_status = {
            "status": "healthy",
            "providers": {},
            "capabilities": {
                "chat": [],
                "draw": [],
                "speak": []
            }
        }
        
        for name, provider in self.providers.items():
            provider_status = {
                "enabled": True,
                "capabilities": [cap.value for cap in provider.capabilities]
            }
            health_status["providers"][name] = provider_status
            
            # Add to capability lists
            for cap in provider.capabilities:
                health_status["capabilities"][cap.value].append(name)
        
        return health_status
    
    async def close(self):
        """Close all provider connections."""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()


# Global manager instance
manager = ProviderManager()