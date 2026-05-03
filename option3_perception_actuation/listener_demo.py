"""
listener_demo.py: Main entry point for the LISTENER demo.

Starts the listener with an HTTP endpoint to trigger pull_now manually.
"""

import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path

from listener.config import load_config
from listener.agency_client import AgencyClient
from listener.storage import EventStore
from listener.listener import Listener

# Shared listener instance (ugly but simple for demo).
_listener: Listener | None = None
_store: EventStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI app."""
    global _listener, _store
    
    # Startup
    config = load_config("listener/config.yaml")
    
    primary_client = AgencyClient(
        agency_url=str(config.primary_service.url),
        agency_name=config.primary_service.name,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
    )
    
    secondary_client = AgencyClient(
        agency_url=str(config.secondary_service.url),
        agency_name=config.secondary_service.name,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
    )
    
    _store = EventStore(config.storage_path)
    _listener = Listener(config, primary_client, secondary_client, _store)
    
    await _listener.start()
    
    yield
    
    # Shutdown
    if _listener:
        await _listener.stop()
    if _store:
        _store.close()


app = FastAPI(title="LISTENER - Event Ingestion Service", lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check endpoint."""
    if _listener and _listener._running:
        return {"status": "ok", "listener": "running"}
    return {"status": "degraded", "listener": "not running"}


@app.post("/pull_now")
async def trigger_pull_now():
    """Manually trigger an immediate pull (for demo purposes)."""
    if not _listener:
        return {"status": "error", "message": "Listener not initialized"}
    return await _listener.pull_now()


@app.get("/")
async def root():
    """Root endpoint with demo instructions."""
    return {
        "message": "LISTENER - Event Ingestion Service",
        "endpoints": {
            "health": "GET /health - Health check",
            "pull_now": "POST /pull_now - Trigger immediate event pull",
        },
        "demo_commands": [
            "curl http://127.0.0.1:8000/health",
            "curl -X POST http://127.0.0.1:8000/pull_now",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
