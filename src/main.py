"""FastAPI application for April Core service."""

import uuid
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .core.manager import manager
from .core.logging import loki_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("April Core API starting up...")
    print(f"Initialized with {len(manager.providers)} providers")
    yield
    # Shutdown
    print("April Core API shutting down...")
    await manager.close()
    await loki_logger.close()


# Request/Response models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Temperature for response generation")


class DrawRequest(BaseModel):
    prompt: str = Field(..., description="Image generation prompt")
    size: Optional[str] = Field("1024x1024", description="Image size")
    quality: Optional[str] = Field("standard", description="Image quality")
    n: Optional[int] = Field(1, description="Number of images to generate")


class SpeakRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    voice: Optional[str] = Field(None, description="Voice ID to use")
    stability: Optional[float] = Field(0.5, description="Voice stability")
    similarity_boost: Optional[float] = Field(0.5, description="Similarity boost")
    style: Optional[float] = Field(0.0, description="Style setting")
    use_speaker_boost: Optional[bool] = Field(True, description="Use speaker boost")


class APIResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


# Create FastAPI app
app = FastAPI(
    title="April Core API",
    description="AI service orchestration with multi-provider support",
    version="2.0.0",
    lifespan=lifespan
)


def get_user_id(x_user_id: str = Header(None)) -> str:
    """Extract user ID from header or generate a new one."""
    if x_user_id:
        return x_user_id
    return str(uuid.uuid4())


@app.post("/chat", response_model=APIResponse)
async def chat_endpoint(
    request: ChatRequest,
    user_id: str = Header(None, alias="X-User-ID")
):
    """Handle chat completion requests."""
    user_id = user_id or str(uuid.uuid4())
    
    try:
        # Convert Pydantic models to dicts
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        response = await manager.chat(
            messages=messages,
            user_id=user_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return APIResponse(
            success=response.success,
            data=response.data,
            error=response.error,
            provider=response.provider,
            model=response.model,
            usage=response.usage
        )
        
    except Exception as e:
        await loki_logger.log_error(user_id, "/chat", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/draw", response_model=APIResponse)
async def draw_endpoint(
    request: DrawRequest,
    user_id: str = Header(None, alias="X-User-ID")
):
    """Handle image generation requests."""
    user_id = user_id or str(uuid.uuid4())
    
    try:
        response = await manager.draw(
            prompt=request.prompt,
            user_id=user_id,
            size=request.size,
            quality=request.quality,
            n=request.n
        )
        
        return APIResponse(
            success=response.success,
            data=response.data,
            error=response.error,
            provider=response.provider,
            model=response.model,
            usage=response.usage
        )
        
    except Exception as e:
        await loki_logger.log_error(user_id, "/draw", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/speak", response_model=APIResponse)
async def speak_endpoint(
    request: SpeakRequest,
    user_id: str = Header(None, alias="X-User-ID")
):
    """Handle text-to-speech requests."""
    user_id = user_id or str(uuid.uuid4())
    
    try:
        response = await manager.speak(
            text=request.text,
            user_id=user_id,
            voice=request.voice,
            stability=request.stability,
            similarity_boost=request.similarity_boost,
            style=request.style,
            use_speaker_boost=request.use_speaker_boost
        )
        
        return APIResponse(
            success=response.success,
            data=response.data,
            error=response.error,
            provider=response.provider,
            model=response.model,
            usage=response.usage
        )
        
    except Exception as e:
        await loki_logger.log_error(user_id, "/speak", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_endpoint():
    """Health check endpoint."""
    try:
        health_status = await manager.get_health()
        return health_status
    except Exception as e:
        await loki_logger.log_error(None, "/health", str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)