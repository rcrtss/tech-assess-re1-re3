"""
Unit tests for listener.listener module.

Tests:
- Listener startup and shutdown
- Pull and persist with dedup
- Fallback trigger on primary failure
- Recovery when primary returns
- pull_now endpoint
- Concurrent pulls are serialized (asyncio.Lock)
- Listener restart does not create duplicates
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile

from listener.listener import Listener
from listener.agency_client import AgencyClient
from listener.storage import EventStore
from listener.models import ClientSeismicEvent
from listener.config import ListenerConfig, ExternalServiceConfig, PullNowEndpoint


@pytest.fixture
def sample_event():
    """Provide a sample seismic event."""
    return ClientSeismicEvent(
        eid=1,
        timestamp=datetime(2024, 5, 3, 12, 0, 0, tzinfo=timezone.utc),
        lat=35.5,
        lon=139.8,
        depth=-10.5,
        Mw=5.2,
        dist=100.0,
        azi=45.0,
        loclat=36.0,
        loclon=140.0,
    )


@pytest.fixture
def sample_event_2():
    """Provide another sample seismic event."""
    return ClientSeismicEvent(
        eid=2,
        timestamp=datetime(2024, 5, 3, 12, 10, 0, tzinfo=timezone.utc),
        lat=36.0,
        lon=140.0,
        depth=-15.0,
        Mw=4.8,
        dist=120.0,
        azi=60.0,
        loclat=36.5,
        loclon=140.5,
    )


@pytest.fixture
def config():
    """Provide a minimal ListenerConfig."""
    return ListenerConfig(
        pull_now_endpoint=PullNowEndpoint(host="127.0.0.1", port=8000),
        m=1,
        lookback_window_minutes=5,
        liveness_threshold_minutes=10,
        timeout_seconds=5.0,
        max_retries=2,
        health_probe_interval_seconds=1.0,
        storage_path=":memory:",
        primary_service=ExternalServiceConfig(
            name="Agency A",
            url="http://127.0.0.1:8001",
        ),
        secondary_service=ExternalServiceConfig(
            name="Agency B",
            url="http://127.0.0.1:8002",
        ),
    )


@pytest.fixture
def temp_db():
    """Provide a temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        yield db_path


@pytest.fixture
def primary_client():
    """Mock primary agency client."""
    client = Mock(spec=AgencyClient)
    client.agency_name = "Agency A"
    return client


@pytest.fixture
def secondary_client():
    """Mock secondary agency client."""
    client = Mock(spec=AgencyClient)
    client.agency_name = "Agency B"
    return client


@pytest.fixture
def store(temp_db):
    """Provide an EventStore instance."""
    return EventStore(temp_db)


@pytest.fixture
def listener(config, primary_client, secondary_client, store):
    """Provide a Listener instance."""
    return Listener(
        config=config,
        primary_client=primary_client,
        secondary_client=secondary_client,
        store=store,
    )


class TestListener:
    """Tests for Listener class."""

    @pytest.mark.asyncio
    async def test_start_and_stop(self, listener):
        """should start and stop without errors."""
        # Configure clients to avoid actual calls.
        listener.primary_client.fetch_since.return_value = []
        
        await listener.start()
        assert listener._running is True
        
        await asyncio.sleep(0.1)  # Let tasks start.
        
        await listener.stop()
        assert listener._running is False

    @pytest.mark.asyncio
    async def test_cannot_start_twice(self, listener):
        """should raise error if already running."""
        listener.primary_client.fetch_since.return_value = []
        
        await listener.start()
        
        with pytest.raises(RuntimeError):
            await listener.start()
        
        await listener.stop()

    @pytest.mark.asyncio
    async def test_pull_persists_events(self, listener, sample_event):
        """should fetch and persist events."""
        listener.primary_client.fetch_since.return_value = [sample_event]
        listener.primary_client.health.return_value = True
        
        await listener._pull()
        
        listener.primary_client.fetch_since.assert_called_once()
        assert listener.store.exists(sample_event.eid)

    @pytest.mark.asyncio
    async def test_pull_deduplicates(self, listener, sample_event):
        """should not insert duplicate events on restart."""
        listener.primary_client.fetch_since.return_value = [sample_event]
        listener.primary_client.health.return_value = True
        
        # First pull.
        await listener._pull()
        first_count = len(listener.store.recent(10))
        
        # Second pull (duplicate).
        await listener._pull()
        second_count = len(listener.store.recent(10))
        
        assert first_count == second_count == 1

    @pytest.mark.asyncio
    async def test_pull_triggers_failover_on_primary_failure(self, listener, sample_event):
        """should switch to secondary when primary fails."""
        listener.primary_client.fetch_since.side_effect = RuntimeError("Connection failed")
        listener.secondary_client.fetch_since.return_value = [sample_event]
        listener.secondary_client.health.return_value = True
        
        await listener._pull()
        
        assert not listener.policy.is_primary_active()
        assert listener.store.exists(sample_event.eid)

    @pytest.mark.asyncio
    async def test_pull_recovers_to_primary(self, listener, sample_event):
        """should recover to primary when it becomes healthy."""
        # First fail on primary and fallback to secondary.
        listener.primary_client.fetch_since.side_effect = RuntimeError("Connection failed")
        listener.primary_client.health.return_value = False
        listener.secondary_client.fetch_since.return_value = [sample_event]
        listener.secondary_client.health.return_value = True
        
        await listener._pull()
        assert not listener.policy.is_primary_active()
        
        # Now simulate primary recovery.
        listener.primary_client.fetch_since.side_effect = None
        listener.primary_client.fetch_since.return_value = []
        listener.primary_client.health.return_value = True
        
        await listener._pull()
        assert listener.policy.is_primary_active()

    @pytest.mark.asyncio
    async def test_pull_now_succeeds(self, listener, sample_event):
        """should execute pull_now and return success."""
        listener.primary_client.fetch_since.return_value = [sample_event]
        listener.primary_client.health.return_value = True
        
        await listener.start()
        result = await listener.pull_now()
        await listener.stop()
        
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_pull_now_fails_when_not_running(self, listener):
        """should return error if listener not running."""
        result = await listener.pull_now()
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_concurrent_pulls_are_serialized(self, listener, sample_event):
        """should prevent concurrent pulls via asyncio.Lock."""
        listener.primary_client.fetch_since.return_value = [sample_event]
        listener.primary_client.health.return_value = True
        
        # Verify that lock exists and is an asyncio.Lock.
        assert hasattr(listener, '_pull_lock')
        assert isinstance(listener._pull_lock, asyncio.Lock)
        
        # Trigger two pulls concurrently.
        task1 = asyncio.create_task(listener._pull())
        task2 = asyncio.create_task(listener._pull())
        
        # Both should complete without errors.
        await asyncio.gather(task1, task2)
        
        # Verify both calls were made (the second is a dedup, so only 1 inserted).
        recent = listener.store.recent(10)
        assert len(recent) == 1
        assert recent[0].eid == sample_event.eid

    @pytest.mark.asyncio
    async def test_multiple_events_inserted(self, listener, sample_event, sample_event_2):
        """should insert multiple events in one pull."""
        listener.primary_client.fetch_since.return_value = [sample_event, sample_event_2]
        listener.primary_client.health.return_value = True
        
        await listener._pull()
        
        assert listener.store.exists(sample_event.eid)
        assert listener.store.exists(sample_event_2.eid)

    @pytest.mark.asyncio
    async def test_pull_both_agencies_fail(self, listener):
        """should handle case when both agencies are unavailable."""
        listener.primary_client.fetch_since.side_effect = RuntimeError("Connection failed")
        listener.secondary_client.fetch_since.side_effect = RuntimeError("Connection failed")
        
        # Should not raise, but log error and stay alive.
        await listener._pull()
        
        # Listener should remain running.
        assert not listener.policy.is_primary_active()  # Switched to secondary
