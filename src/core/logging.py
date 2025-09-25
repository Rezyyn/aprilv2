"""Logging utilities with Loki integration for per-user memory logging."""

import json
import time
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from .config import get_config


class LokiLogger:
    """Logger that sends logs to Loki for centralized logging."""
    
    def __init__(self):
        config = get_config()
        self.enabled = config.logging.loki.enabled
        self.loki_url = config.logging.loki.url
        self.base_labels = config.logging.loki.labels
        self.client = httpx.AsyncClient(timeout=10.0) if self.enabled else None
    
    async def log_user_interaction(
        self,
        user_id: str,
        endpoint: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        provider: str,
        model: str,
        duration_ms: float
    ):
        """Log user interaction for memory tracking."""
        if not self.enabled:
            return
        
        timestamp = int(time.time() * 1_000_000_000)  # nanoseconds
        
        log_entry = {
            "user_id": user_id,
            "endpoint": endpoint,
            "provider": provider,
            "model": model,
            "duration_ms": duration_ms,
            "request": request_data,
            "response": response_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        labels = {
            **self.base_labels,
            "user_id": user_id,
            "endpoint": endpoint,
            "provider": provider,
            "model": model
        }
        
        # Format labels for Loki
        label_string = ",".join([f'{k}="{v}"' for k, v in labels.items()])
        
        loki_entry = {
            "streams": [
                {
                    "stream": labels,
                    "values": [
                        [str(timestamp), json.dumps(log_entry)]
                    ]
                }
            ]
        }
        
        try:
            await self.client.post(
                f"{self.loki_url}/loki/api/v1/push",
                json=loki_entry,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            # Don't fail the request if logging fails
            print(f"Failed to send log to Loki: {e}")
    
    async def log_error(
        self,
        user_id: Optional[str],
        endpoint: str,
        error: str,
        details: Dict[str, Any] = None
    ):
        """Log errors."""
        if not self.enabled:
            return
        
        timestamp = int(time.time() * 1_000_000_000)
        
        log_entry = {
            "level": "error",
            "user_id": user_id,
            "endpoint": endpoint,
            "error": error,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        labels = {
            **self.base_labels,
            "level": "error",
            "endpoint": endpoint
        }
        
        if user_id:
            labels["user_id"] = user_id
        
        loki_entry = {
            "streams": [
                {
                    "stream": labels,
                    "values": [
                        [str(timestamp), json.dumps(log_entry)]
                    ]
                }
            ]
        }
        
        try:
            await self.client.post(
                f"{self.loki_url}/loki/api/v1/push",
                json=loki_entry,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            print(f"Failed to send error log to Loki: {e}")
    
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()


# Global logger instance
loki_logger = LokiLogger()