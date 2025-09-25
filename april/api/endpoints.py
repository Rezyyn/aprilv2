"""FastAPI endpoints for April v2."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import structlog

from ..core.manager import AprilManager
from ..providers.base import ChatRequest, ImageRequest, SpeechRequest
from ..config.settings import settings

logger = structlog.get_logger()

# Router for API endpoints
router = APIRouter()

# Global manager instance (will be initialized on startup)
manager: Optional[AprilManager] = None


async def get_manager() -> AprilManager:
    """Dependency to get the manager instance."""
    if manager is None:
        raise HTTPException(status_code=500, detail="Manager not initialized")
    return manager


@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    april: AprilManager = Depends(get_manager)
):
    """Chat with AI using LLM providers."""
    try:
        response = await april.chat(request)
        return {
            "success": True,
            "data": response.model_dump()
        }
    except Exception as e:
        logger.error("Chat endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/draw")
async def draw_endpoint(
    request: ImageRequest,
    april: AprilManager = Depends(get_manager)
):
    """Generate images using image providers."""
    try:
        response = await april.generate_image(request)
        return {
            "success": True,
            "data": response.model_dump()
        }
    except Exception as e:
        logger.error("Draw endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speak")
async def speak_endpoint(
    request: SpeechRequest,
    april: AprilManager = Depends(get_manager)
):
    """Generate speech using TTS providers."""
    try:
        response = await april.synthesize_speech(request)
        return {
            "success": True,
            "data": response.model_dump()
        }
    except Exception as e:
        logger.error("Speak endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def status_endpoint(april: AprilManager = Depends(get_manager)):
    """Get system status and provider information."""
    try:
        status = april.get_provider_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error("Status endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/persona")
async def set_user_persona_endpoint(
    user_id: str,
    persona: str,
    april: AprilManager = Depends(get_manager)
):
    """Set persona for a specific user."""
    try:
        april.set_user_persona(user_id, persona)
        return {
            "success": True,
            "message": f"Persona set for user {user_id}"
        }
    except Exception as e:
        logger.error("Set persona endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_endpoint():
    """Health check endpoint."""
    return {"status": "healthy", "service": "april-v2"}