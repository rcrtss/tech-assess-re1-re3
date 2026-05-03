"""
Listener: Event ingestion service with fallback and recovery logic.

Responsibilities:
- Poll agencies at regular intervals via internal timer.
- Expose on-demand pull endpoint for external triggering (orchestrator).
- Manage fallback to secondary when primary is unavailable.
- Periodically check primary health and recover when available.
- Validate and persist events to storage with dedup.
- Prevent overlapping pulls via asyncio.Lock.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from listener.agency_client import AgencyClient
from listener.fallback import FallbackPolicy
from listener.storage import EventStore
from listener.config import ListenerConfig
from listener.logging_setup import configure_logging

logger = configure_logging(__name__)


class Listener:
    """
    Event ingestion listener with fallback and recovery logic.
    
    Polls agencies, manages failover, validates and persists seismic events.
    """

    def __init__(
        self,
        config: ListenerConfig,
        primary_client: AgencyClient,
        secondary_client: AgencyClient,
        store: EventStore,
    ):
        """
        Initialize the listener.
        
        Args:
            config: ListenerConfig instance.
            primary_client: AgencyClient for the primary agency.
            secondary_client: AgencyClient for the secondary agency.
            store: EventStore instance for persistence.
        """
        self.config = config
        self.primary_client = primary_client
        self.secondary_client = secondary_client
        self.store = store
        
        self.policy = FallbackPolicy(
            primary_name=config.primary_service.name,
            secondary_name=config.secondary_service.name,
        )
        
        self._pull_lock = asyncio.Lock()
        self._running = False
        self._last_successful_pull: Optional[datetime] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        logger.info("Listener initialized")


    async def start(self) -> None:
        """
        Start the listener: polling timer and health check loop.
        
        Raises:
            RuntimeError: If listener is already running.
        """
        if self._running:
            raise RuntimeError("Listener is already running")
        
        self._running = True
        logger.info("Listener starting")
        
        self._poll_task = asyncio.create_task(self._poll_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info("Listener started")

    async def stop(self) -> None:
        """
        Stop the listener gracefully.
        
        Cancels polling and health check tasks.
        """
        if not self._running:
            logger.warning("Listener is not running")
            return
        
        logger.info("Listener stopping")
        self._running = False
        
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Listener stopped")

    async def pull_now(self) -> dict:
        """
        Trigger an immediate pull (external hook for orchestrator).
        
        Returns:
            Dict with pull result: {"status": "ok"} or {"status": "error", "message": "..."}.
        """
        if not self._running:
            return {"status": "error", "message": "Listener is not running"}
        
        try:
            await self._pull()
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"pull_now failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _poll_loop(self) -> None:
        """
        Main polling loop: pull at regular intervals.
        """
        # DEMO: poll_interval_minutes is interpreted as seconds for rapid demo execution.
        # In production, would be: poll_interval_seconds = self.config.poll_interval_minutes * 60
        poll_interval_seconds = self.config.poll_interval_minutes
        
        while self._running:
            try:
                await self._pull()
            except Exception as e:
                logger.error(f"Poll cycle failed: {e}")
            
            try:
                await asyncio.sleep(poll_interval_seconds)
            except asyncio.CancelledError:
                break

    async def _health_check_loop(self) -> None:
        """
        Periodic health check of primary when using secondary.
        """
        probe_interval = self.config.health_probe_interval_seconds
        
        while self._running:
            try:
                if not self.policy.is_primary_active():
                    # Currently using secondary, check primary.
                    is_primary_healthy = self.primary_client.health()
                    if is_primary_healthy:
                        self.policy.on_recovery()
                
                await asyncio.sleep(probe_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                try:
                    await asyncio.sleep(probe_interval)
                except asyncio.CancelledError:
                    break

    async def _pull(self) -> None:
        """
        Pull events from the active agency with fallback logic.
        
        Uses asyncio.Lock to prevent concurrent pulls from timer and pull_now.
        """
        async with self._pull_lock:
            await self._pull_protected()

    async def _pull_protected(self) -> None:
        """
        Protected pull: fetch, validate, and persist events.
        """
        now = datetime.now(timezone.utc)
        
        # Calculate lookback window: wider than poll_interval to ensure overlap.
        # DEMO: lookback_window_minutes is interpreted as seconds for rapid demo execution.
        # In production, would use: timedelta(minutes=self.config.lookback_window_minutes)
        if self._last_successful_pull is None:
            # First pull: use full lookback window.
            since = now - timedelta(seconds=self.config.lookback_window_minutes)
        else:
            # Subsequent pulls: lookback wider than poll_interval.
            since = self._last_successful_pull - timedelta(
                seconds=self.config.lookback_window_minutes
            )
        
        # Pick current active agency.
        active_name = self.policy.pick_agency()
        active_client = (
            self.primary_client
            if active_name == self.config.primary_service.name
            else self.secondary_client
        )
        
        try:
            events = active_client.fetch_since(since)
            
            # Persist events with dedup.
            inserted_count = 0
            for event in events:
                if self.store.add(event):
                    inserted_count += 1
            
            logger.info(
                f"Pull from {active_name}: fetched {len(events)}, inserted {inserted_count}"
            )
            self._last_successful_pull = now
            
            # If using secondary and it succeeded, still probe primary.
            if not self.policy.is_primary_active():
                is_primary_healthy = self.primary_client.health()
                if is_primary_healthy:
                    self.policy.on_recovery()
        
        except Exception as e:
            logger.error(f"Failed to pull from {active_name}: {e}")
            
            # If primary failed, switch to secondary.
            if self.policy.is_primary_active():
                self.policy.on_failure()
                
                # Retry once with secondary.
                try:
                    active_name = self.policy.pick_agency()
                    active_client = self.secondary_client
                    
                    events = active_client.fetch_since(since)
                    inserted_count = 0
                    for event in events:
                        if self.store.add(event):
                            inserted_count += 1
                    
                    logger.info(
                        f"Fallback to {active_name}: fetched {len(events)}, inserted {inserted_count}"
                    )
                    self._last_successful_pull = now
                
                except Exception as e2:
                    logger.error(f"Fallback to {active_name} also failed: {e2}")