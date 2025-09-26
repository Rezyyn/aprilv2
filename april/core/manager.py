"""Core manager for April v2 - orchestrates providers and manages user interactions."""

import random
from typing import Dict, List, Optional, Any
import structlog

from ..config.settings import Settings
from ..providers.base import (
    BaseProvider,
    LLMProvider,
    ImageProvider,
    SpeechProvider,
    ChatRequest,
    ChatResponse,
    ImageRequest,
    ImageResponse,
    SpeechRequest,
    SpeechResponse,
)
from ..providers.openai_provider import OpenAILLMProvider, OpenAIImageProvider
from ..providers.anthropic_provider import AnthropicLLMProvider
from ..providers.deepseek_provider import DeepSeekLLMProvider, DeepSeekImageProvider
from ..providers.elevenlabs_provider import ElevenLabsSpeechProvider

logger = structlog.get_logger()


class AprilManager:
    """Core manager that orchestrates providers and handles user interactions."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm_providers: Dict[str, LLMProvider] = {}
        self.image_providers: Dict[str, ImageProvider] = {}
        self.speech_providers: Dict[str, SpeechProvider] = {}
        self.user_memories: Dict[str, List[Dict[str, Any]]] = {}
        self.user_personas: Dict[str, str] = {}
    
    async def initialize(self) -> None:
        """Initialize all providers based on configuration."""
        if not self.settings.providers:
            logger.warning("No providers configuration found")
            return
        
        # Initialize LLM providers
        for name, config in self.settings.providers.llm.items():
            if not config.enabled:
                continue
                
            try:
                provider = self._create_llm_provider(name, config.model_dump())
                if provider and await provider.is_available():
                    self.llm_providers[name] = provider
                    logger.info("Initialized LLM provider", provider=name)
                else:
                    logger.warning("LLM provider not available", provider=name)
            except Exception as e:
                logger.error("Failed to initialize LLM provider", provider=name, error=str(e))
        
        # Initialize image providers
        for name, config in self.settings.providers.image.items():
            if not config.enabled:
                continue
                
            try:
                provider = self._create_image_provider(name, config.model_dump())
                if provider and await provider.is_available():
                    self.image_providers[name] = provider
                    logger.info("Initialized image provider", provider=name)
                else:
                    logger.warning("Image provider not available", provider=name)
            except Exception as e:
                logger.error("Failed to initialize image provider", provider=name, error=str(e))
        
        # Initialize speech providers
        for name, config in self.settings.providers.speech.items():
            if not config.enabled:
                continue
                
            try:
                provider = self._create_speech_provider(name, config.model_dump())
                if provider and await provider.is_available():
                    self.speech_providers[name] = provider
                    logger.info("Initialized speech provider", provider=name)
                else:
                    logger.warning("Speech provider not available", provider=name)
            except Exception as e:
                logger.error("Failed to initialize speech provider", provider=name, error=str(e))
    
    def _create_llm_provider(self, name: str, config: Dict[str, Any]) -> Optional[LLMProvider]:
        """Create LLM provider based on name."""
        if name == "openai":
            return OpenAILLMProvider(name, config)
        elif name == "claude":
            return AnthropicLLMProvider(name, config)
        elif name == "deepseek":
            return DeepSeekLLMProvider(name, config)
        else:
            logger.warning("Unknown LLM provider", provider=name)
            return None
    
    def _create_image_provider(self, name: str, config: Dict[str, Any]) -> Optional[ImageProvider]:
        """Create image provider based on name."""
        if name == "openai":
            return OpenAIImageProvider(name, config)
        elif name == "deepseek":
            return DeepSeekImageProvider(name, config)
        else:
            logger.warning("Unknown image provider", provider=name)
            return None
    
    def _create_speech_provider(self, name: str, config: Dict[str, Any]) -> Optional[SpeechProvider]:
        """Create speech provider based on name."""
        if name == "elevenlabs":
            return ElevenLabsSpeechProvider(name, config)
        else:
            logger.warning("Unknown speech provider", provider=name)
            return None
    
    def _select_provider(self, providers: Dict[str, BaseProvider]) -> Optional[BaseProvider]:
        """Select a provider based on weights."""
        if not providers:
            return None
        
        # Simple weighted random selection
        weights = [provider.weight for provider in providers.values()]
        if sum(weights) == 0:
            # If no weights, select randomly
            return random.choice(list(providers.values()))
        
        provider_list = list(providers.values())
        selected = random.choices(provider_list, weights=weights, k=1)[0]
        return selected
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Handle chat request with LLM routing."""
        # Apply persona and memory if user_id is provided
        if request.user_id:
            request = await self._apply_user_context(request)
        
        # Select LLM provider
        provider = self._select_provider(self.llm_providers)
        if not provider:
            raise RuntimeError("No LLM providers available")
        
        logger.info("Routing chat request", provider=provider.name, user_id=request.user_id)
        
        try:
            response = await provider.chat(request)
            
            # Store interaction in memory
            if request.user_id:
                await self._store_memory(request.user_id, request, response)
            
            return response
        except Exception as e:
            logger.error("Chat request failed", provider=provider.name, error=str(e))
            # Try fallback provider if available
            remaining_providers = {
                name: p for name, p in self.llm_providers.items() 
                if name != provider.name
            }
            if remaining_providers:
                fallback_provider = self._select_provider(remaining_providers)
                logger.info("Trying fallback provider", provider=fallback_provider.name)
                return await fallback_provider.chat(request)
            raise
    
    async def generate_image(self, request: ImageRequest) -> ImageResponse:
        """Handle image generation request."""
        provider = self._select_provider(self.image_providers)
        if not provider:
            raise RuntimeError("No image providers available")
        
        logger.info("Routing image request", provider=provider.name, user_id=request.user_id)
        
        return await provider.generate(request)
    
    async def synthesize_speech(self, request: SpeechRequest) -> SpeechResponse:
        """Handle speech synthesis request."""
        provider = self._select_provider(self.speech_providers)
        if not provider:
            raise RuntimeError("No speech providers available")
        
        logger.info("Routing speech request", provider=provider.name, user_id=request.user_id)
        
        return await provider.synthesize(request)
    
    async def _apply_user_context(self, request: ChatRequest) -> ChatRequest:
        """Apply user persona and memory to the request."""
        user_id = request.user_id
        if not user_id:
            return request
        
        # Get user persona
        persona = self.user_personas.get(user_id, "helpful_assistant")
        
        # Get recent memory
        memory = self.user_memories.get(user_id, [])
        recent_memory = memory[-5:] if memory else []  # Last 5 interactions
        
        # Modify system message to include persona and memory context
        messages = request.messages.copy()
        
        # Find or create system message
        system_message_idx = None
        for i, msg in enumerate(messages):
            if msg.role == "system":
                system_message_idx = i
                break
        
        # Construct enhanced system message
        system_content = f"You are {persona}."
        
        if recent_memory:
            memory_context = "Recent conversation context:\n"
            for interaction in recent_memory:
                if "user_message" in interaction:
                    memory_context += f"User: {interaction['user_message']}\n"
                if "assistant_response" in interaction:
                    memory_context += f"Assistant: {interaction['assistant_response']}\n"
            system_content += f"\n\n{memory_context}"
        
        if system_message_idx is not None:
            # Update existing system message
            messages[system_message_idx].content = system_content
        else:
            # Add new system message at the beginning
            from ..providers.base import ChatMessage
            system_msg = ChatMessage(role="system", content=system_content)
            messages.insert(0, system_msg)
        
        return ChatRequest(
            messages=messages,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            user_id=request.user_id
        )
    
    async def _store_memory(self, user_id: str, request: ChatRequest, response: ChatResponse) -> None:
        """Store interaction in user memory."""
        if user_id not in self.user_memories:
            self.user_memories[user_id] = []
        
        # Find the last user message
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
        
        interaction = {
            "timestamp": "now",  # In real implementation, use proper timestamp
            "user_message": user_message,
            "assistant_response": response.content,
            "provider": response.provider,
            "model": response.model
        }
        
        self.user_memories[user_id].append(interaction)
        
        # Keep only last 50 interactions per user
        if len(self.user_memories[user_id]) > 50:
            self.user_memories[user_id] = self.user_memories[user_id][-50:]
    
    def set_user_persona(self, user_id: str, persona: str) -> None:
        """Set persona for a user."""
        self.user_personas[user_id] = persona
        logger.info("Set user persona", user_id=user_id, persona=persona)
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        return {
            "llm_providers": list(self.llm_providers.keys()),
            "image_providers": list(self.image_providers.keys()),
            "speech_providers": list(self.speech_providers.keys()),
            "total_users": len(self.user_memories),
        }