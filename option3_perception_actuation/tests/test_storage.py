"""
Unit tests for listener.storage module.

Tests:
- EventStore initialization and schema creation
- Adding events and deduplication
- Checking event existence
- Retrieving recent events
"""

import pytest
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from listener.storage import EventStore
from listener.models import ClientSeismicEvent


@pytest.fixture
def temp_db():
    """Provide a temporary database path and clean up after."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        yield db_path


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


class TestEventStore:
    """Tests for EventStore class."""

    def test_init_creates_database(self, temp_db):
        """should initialize database and create schema."""
        store = EventStore(temp_db)
        assert Path(temp_db).exists()
        store.close()

    def test_add_single_event(self, temp_db, sample_event):
        """should add a single event successfully."""
        store = EventStore(temp_db)
        inserted = store.add(sample_event)
        assert inserted is True
        store.close()

    def test_add_duplicate_event_returns_false(self, temp_db, sample_event):
        """should not re-insert duplicate event (same eid)."""
        store = EventStore(temp_db)
        inserted1 = store.add(sample_event)
        inserted2 = store.add(sample_event)
        assert inserted1 is True
        assert inserted2 is False
        store.close()

    def test_deduplication_by_eid(self, temp_db, sample_event):
        """should deduplicate events by eid, ignoring timestamp differences."""
        store = EventStore(temp_db)
        
        # Add original event.
        inserted1 = store.add(sample_event)
        assert inserted1 is True
        
        # Create a new event with same eid but different timestamp.
        duplicate = ClientSeismicEvent(
            eid=1,
            timestamp=datetime(2024, 5, 3, 14, 0, 0, tzinfo=timezone.utc),
            lat=35.5,
            lon=139.8,
            depth=-10.5,
            Mw=5.2,
            dist=100.0,
            azi=45.0,
            loclat=36.0,
            loclon=140.0,
        )
        
        # Should not insert the duplicate.
        inserted2 = store.add(duplicate)
        assert inserted2 is False
        
        store.close()

    def test_exists_returns_true_for_existing_event(self, temp_db, sample_event):
        """should return True for existing event."""
        store = EventStore(temp_db)
        store.add(sample_event)
        assert store.exists(sample_event.eid) is True
        store.close()

    def test_exists_returns_false_for_nonexistent_event(self, temp_db, sample_event):
        """should return False for non-existent event."""
        store = EventStore(temp_db)
        store.add(sample_event)
        assert store.exists(999) is False
        store.close()

    def test_recent_returns_empty_for_empty_store(self, temp_db):
        """should return empty list for empty store."""
        store = EventStore(temp_db)
        events = store.recent(10)
        assert events == []
        store.close()

    def test_recent_returns_n_most_recent_events(self, temp_db, sample_event, sample_event_2):
        """should return n most recent events ordered by timestamp descending."""
        store = EventStore(temp_db)
        store.add(sample_event)
        store.add(sample_event_2)
        
        # Retrieve 2 most recent.
        recent = store.recent(2)
        assert len(recent) == 2
        
        # sample_event_2 has later timestamp, so should be first.
        assert recent[0].eid == 2
        assert recent[1].eid == 1
        
        store.close()

    def test_recent_respects_limit(self, temp_db, sample_event, sample_event_2):
        """should return at most n events."""
        store = EventStore(temp_db)
        store.add(sample_event)
        store.add(sample_event_2)
        
        # Request only 1, even though 2 exist.
        recent = store.recent(1)
        assert len(recent) == 1
        
        store.close()

    def test_recent_preserves_event_data(self, temp_db, sample_event):
        """should preserve all event fields when retrieving."""
        store = EventStore(temp_db)
        store.add(sample_event)
        
        recent = store.recent(1)
        assert len(recent) == 1
        
        retrieved = recent[0]
        assert retrieved.eid == sample_event.eid
        assert retrieved.lat == sample_event.lat
        assert retrieved.lon == sample_event.lon
        assert retrieved.depth == sample_event.depth
        assert retrieved.Mw == sample_event.Mw
        assert retrieved.dist == sample_event.dist
        assert retrieved.azi == sample_event.azi
        assert retrieved.loclat == sample_event.loclat
        assert retrieved.loclon == sample_event.loclon
        
        store.close()

    def test_context_manager(self, temp_db, sample_event):
        """should work as context manager."""
        with EventStore(temp_db) as store:
            store.add(sample_event)
            assert store.exists(sample_event.eid)
        
        # Reconnect and verify data persisted.
        with EventStore(temp_db) as store:
            assert store.exists(sample_event.eid)

    def test_multiple_events_different_eids(self, temp_db):
        """should handle multiple events with different eids."""
        store = EventStore(temp_db)
        
        events = [
            ClientSeismicEvent(
                eid=i,
                timestamp=datetime(2024, 5, 3, 12, i, 0, tzinfo=timezone.utc),
                lat=35.0 + i,
                lon=139.0 + i,
                depth=-10.0 - i,
                Mw=5.0 + i * 0.1,
                dist=100.0 + i * 10,
                azi=45.0 + i * 10,
                loclat=36.0 + i,
                loclon=140.0 + i,
            )
            for i in range(5)
        ]
        
        for event in events:
            inserted = store.add(event)
            assert inserted is True
        
        # All should exist.
        for event in events:
            assert store.exists(event.eid) is True
        
        # Retrieve all 5.
        recent = store.recent(10)
        assert len(recent) == 5
        
        store.close()
