"""
Endpoints:
- GET /events?since=<timestamp>: return all events since the given timestamp
- GET /health: return status: 
    - 200 OK if the primary agency is healthy, 
    - 503 Service Unavailable if in failover mode and secondary is healthy, 
    - 500 Internal Server Error if both are unhealthy.
"""
from fastapi import FastAPI
from datetime import datetime
from agencies.event_data import EVENTS
from agencies.models import ServerSeismicEvent
import asyncio

app = FastAPI(title="Seismic Event API", description="Agency A: Simulated seismic event data provider")

SIMULATED_DELAY = 0.5

@app.get("/")
async def root():
    return {"message": "Welcome to the Seismic Event API. Use /events?since=<timestamp> to get recent events."}

@app.get("/events", response_model=list[ServerSeismicEvent])
async def get_events(since: datetime | None = None):
    """Return events newer than `since`. If `since` is omitted, return all events."""
    await asyncio.sleep(SIMULATED_DELAY)
    if since is not None and since.tzinfo is None:
        raise ValueError("invalid timestamp: should be localized (UTC)")
    return [e for e in EVENTS if since is None or e.timestamp > since]

@app.get("/health")
async def health():
    """Basic health check endpoint."""
    return {"status": "ok"}