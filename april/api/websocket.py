"""WebSocket endpoints for real-time communication."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import structlog

from ..core.manager import AprilManager
from ..providers.base import ChatMessage, ChatRequest

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info("WebSocket connected", user_id=user_id)
    
    def disconnect(self, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info("WebSocket disconnected", user_id=user_id)
    
    async def send_message(self, user_id: str, message: dict):
        """Send message to a specific user."""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users."""
        for websocket in self.active_connections.values():
            await websocket.send_text(json.dumps(message))


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, user_id: str, april: AprilManager):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "chat")
                
                if message_type == "chat":
                    # Handle chat message
                    content = message_data.get("content", "")
                    if not content:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Empty message content"
                        }))
                        continue
                    
                    # Create chat request
                    chat_request = ChatRequest(
                        messages=[ChatMessage(role="user", content=content)],
                        user_id=user_id
                    )
                    
                    # Send typing indicator
                    await websocket.send_text(json.dumps({
                        "type": "typing",
                        "status": True
                    }))
                    
                    try:
                        # Get response from AI
                        response = await april.chat(chat_request)
                        
                        # Send response
                        await websocket.send_text(json.dumps({
                            "type": "message",
                            "content": response.content,
                            "provider": response.provider,
                            "model": response.model,
                            "usage": response.usage
                        }))
                        
                    except Exception as e:
                        logger.error("Chat processing error", error=str(e), user_id=user_id)
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Failed to process message: {str(e)}"
                        }))
                    
                    finally:
                        # Stop typing indicator
                        await websocket.send_text(json.dumps({
                            "type": "typing",
                            "status": False
                        }))
                
                elif message_type == "persona":
                    # Handle persona change
                    persona = message_data.get("persona", "")
                    if persona:
                        april.set_user_persona(user_id, persona)
                        await websocket.send_text(json.dumps({
                            "type": "persona_updated",
                            "persona": persona
                        }))
                
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error("WebSocket message processing error", error=str(e), user_id=user_id)
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error("WebSocket connection error", error=str(e), user_id=user_id)
        manager.disconnect(user_id)