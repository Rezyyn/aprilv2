"""Main FastAPI application for April v2."""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from april.config.settings import settings
from april.core.manager import AprilManager
from april.api.endpoints import router, manager as global_manager


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting April v2")
    
    # Load configuration
    try:
        settings.load_providers_config()
        logger.info("Loaded providers configuration")
    except Exception as e:
        logger.error("Failed to load providers configuration", error=str(e))
        raise
    
    # Initialize manager
    april_manager = AprilManager(settings)
    await april_manager.initialize()
    
    # Set global manager instance
    global global_manager
    import april.api.endpoints
    april.api.endpoints.manager = april_manager
    
    logger.info("April v2 started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down April v2")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="FastAPI backend for April v2 AI assistant",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Add health endpoint at root level too
@app.get("/health")
async def health_root():
    """Health check endpoint at root level."""
    return {"status": "healthy", "service": "april-v2"}

# WebSocket endpoint
from april.api.websocket import websocket_endpoint

@app.websocket("/ws/{user_id}")
async def websocket_handler(websocket, user_id: str):
    """WebSocket endpoint for real-time communication."""
    # Get manager from global scope
    import april.api.endpoints
    april_manager = april.api.endpoints.manager
    if april_manager is None:
        await websocket.close(code=1000, reason="Manager not initialized")
        return
    
    await websocket_endpoint(websocket, user_id, april_manager)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "April v2",
        "version": "0.1.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )