"""
AprilV2 API Server
Provides endpoints for chat, drawing, speech, and health checks.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import yaml
import os

app = FastAPI(title="AprilV2 API", version="1.0.0")

# Request models
class ChatRequest(BaseModel):
    user_id: str
    message: str
    persona: str = "default"

class DrawRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024

class SpeakRequest(BaseModel):
    text: str
    voice: str = "Rachel"

# Response models
class HealthResponse(BaseModel):
    status: str

class ChatResponse(BaseModel):
    response: str
    persona: str
    user_id: str

class DrawResponse(BaseModel):
    image_url: str
    prompt: str
    width: int
    height: int

class SpeakResponse(BaseModel):
    audio_url: str
    voice: str
    text: str

# Load configuration
def load_config():
    """Load configuration from YAML files."""
    config = {}
    providers = {}
    
    if os.path.exists("config.yml"):
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f) or {}
    
    if os.path.exists("providers.yml"):
        with open("providers.yml", "r") as f:
            providers = yaml.safe_load(f) or {}
    
    return config, providers

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that processes messages with specified persona.
    """
    config, providers = load_config()
    
    # Basic validation
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # For now, return a mock response
    # In a real implementation, this would integrate with chat providers
    response_text = f"Hello {request.user_id}! I received your message: '{request.message}'. I'm responding as the '{request.persona}' persona."
    
    return ChatResponse(
        response=response_text,
        persona=request.persona,
        user_id=request.user_id
    )

@app.post("/draw", response_model=DrawResponse)
async def draw(request: DrawRequest):
    """
    Draw endpoint that generates images from text prompts.
    """
    config, providers = load_config()
    
    # Basic validation
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    if request.width <= 0 or request.height <= 0:
        raise HTTPException(status_code=400, detail="Width and height must be positive")
    
    # For now, return a mock response
    # In a real implementation, this would integrate with image generation providers
    mock_image_url = f"https://placeholder.com/{request.width}x{request.height}"
    
    return DrawResponse(
        image_url=mock_image_url,
        prompt=request.prompt,
        width=request.width,
        height=request.height
    )

@app.post("/speak", response_model=SpeakResponse)
async def speak(request: SpeakRequest):
    """
    Speech synthesis endpoint that converts text to speech.
    """
    config, providers = load_config()
    
    # Basic validation
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # For now, return a mock response
    # In a real implementation, this would integrate with TTS providers
    mock_audio_url = f"https://audio.example.com/speech/{hash(request.text + request.voice)}.mp3"
    
    return SpeakResponse(
        audio_url=mock_audio_url,
        voice=request.voice,
        text=request.text
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)