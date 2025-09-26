"""ElevenLabs speech provider implementation."""

import os
from typing import Any, Dict
import tempfile
import uuid

import httpx

from .base import SpeechProvider, SpeechRequest, SpeechResponse


class ElevenLabsSpeechProvider(SpeechProvider):
    """ElevenLabs TTS provider."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = os.getenv(config.get("api_key_env", "ELEVENLABS_API_KEY"))
        self.voices = config.get("voices", [])
        self.base_url = "https://api.elevenlabs.io/v1"
    
    async def is_available(self) -> bool:
        """Check if ElevenLabs is available."""
        if not self.api_key or not self.enabled:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key}
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def synthesize(self, request: SpeechRequest) -> SpeechResponse:
        """Synthesize speech using ElevenLabs."""
        if not self.api_key:
            raise RuntimeError("ElevenLabs API key not configured")
        
        # Choose voice
        voice_id = request.voice
        if not voice_id and self.voices:
            voice_id = self.voices[0]["voice_id"]
        elif not voice_id:
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default Rachel voice
        
        # Extract voice ID if full voice info is provided
        if isinstance(voice_id, dict):
            voice_id = voice_id.get("voice_id", voice_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": request.text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.5
                    }
                }
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"ElevenLabs API error: {response.status_code}")
            
            # Save audio to temporary file
            audio_id = str(uuid.uuid4())
            temp_dir = tempfile.gettempdir()
            audio_path = os.path.join(temp_dir, f"speech_{audio_id}.mp3")
            
            with open(audio_path, "wb") as f:
                f.write(response.content)
            
            # In a real implementation, you'd upload this to a file storage service
            # For now, return the local file path
            audio_url = f"file://{audio_path}"
            
            # Find voice name for response
            voice_name = voice_id
            for voice in self.voices:
                if voice["voice_id"] == voice_id:
                    voice_name = voice["name"]
                    break
            
            return SpeechResponse(
                audio_url=audio_url,
                provider=self.name,
                voice=voice_name
            )