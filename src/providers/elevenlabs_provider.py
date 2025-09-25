"""ElevenLabs provider implementation."""

import httpx
import base64
from typing import Dict, Any, List
from .base import BaseProvider, ProviderResponse, Capability


class ElevenLabsProvider(BaseProvider):
    """ElevenLabs provider for text-to-speech."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("elevenlabs", config)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"xi-api-key": self.api_key},
            timeout=60.0
        )
    
    async def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> ProviderResponse:
        """ElevenLabs doesn't support chat."""
        return ProviderResponse(
            success=False,
            error="Chat capability not supported by ElevenLabs provider",
            provider=self.name,
            model=model
        )
    
    async def draw(self, prompt: str, model: str, **kwargs) -> ProviderResponse:
        """ElevenLabs doesn't support image generation."""
        return ProviderResponse(
            success=False,
            error="Draw capability not supported by ElevenLabs provider",
            provider=self.name,
            model=model
        )
    
    async def speak(self, text: str, model: str, voice: str = None, **kwargs) -> ProviderResponse:
        """Handle text-to-speech using ElevenLabs API."""
        if not self.supports_capability(Capability.SPEAK):
            return ProviderResponse(
                success=False,
                error="Speak capability not supported",
                provider=self.name,
                model=model
            )
        
        try:
            # Use a default voice if none provided
            voice_id = voice or "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
            
            payload = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": kwargs.get("stability", 0.5),
                    "similarity_boost": kwargs.get("similarity_boost", 0.5),
                    "style": kwargs.get("style", 0.0),
                    "use_speaker_boost": kwargs.get("use_speaker_boost", True)
                }
            }
            
            response = await self.client.post(
                f"/text-to-speech/{voice_id}",
                json=payload,
                headers={"Accept": "audio/mpeg"}
            )
            response.raise_for_status()
            
            # Convert audio data to base64 for JSON response
            audio_data = base64.b64encode(response.content).decode('utf-8')
            
            return ProviderResponse(
                success=True,
                data={
                    "audio_base64": audio_data,
                    "content_type": "audio/mpeg",
                    "voice_id": voice_id
                },
                provider=self.name,
                model=model
            )
            
        except Exception as e:
            return ProviderResponse(
                success=False,
                error=str(e),
                provider=self.name,
                model=model
            )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()