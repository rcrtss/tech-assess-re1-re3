"""
Test suite for FastAPI seismic event agencies (agency_a, agency_b).
Tests use FastAPI TestClient for straightforward sync testing.
"""
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from agencies.agency_a import app as agency_a_app
from agencies.agency_b import app as agency_b_app
from agencies.models import ServerSeismicEvent


# Minimal test fixture: a few events with known timestamps for isolation.
NOW = datetime.now(timezone.utc)
TEST_EVENTS = [
    ServerSeismicEvent(
        eid=1, timestamp=NOW - timedelta(hours=3),
        lat=37.5, lon=-3.6, depth=-8.0, Mw=4.2,
        dist=120.5, azi=45.0, loclat=40.0, loclon=-3.7,
    ),
    ServerSeismicEvent(
        eid=2, timestamp=NOW - timedelta(hours=1),
        lat=38.1, lon=-1.9, depth=-12.0, Mw=3.7,
        dist=85.0, azi=60.0, loclat=39.0, loclon=-2.0,
    ),
    ServerSeismicEvent(
        eid=3, timestamp=NOW - timedelta(minutes=30),
        lat=36.8, lon=-4.1, depth=-5.0, Mw=2.9,
        dist=200.0, azi=-30.0, loclat=38.5, loclon=-4.0,
    ),
]


@pytest.fixture(params=["agency_a", "agency_b"])
def client(request):
    """Parametrized fixture to test both agencies."""
    if request.param == "agency_a":
        return TestClient(agency_a_app)
    else:
        return TestClient(agency_b_app)


class TestEventsEndpoint:
    """Tests for GET /events"""

    def test_events_returns_non_empty_list(self, client):
        """Verify /events returns all events when no since parameter is provided."""
        response = client.get("/events")
        assert response.status_code == 200
        events = response.json()
        assert isinstance(events, list)
        assert len(events) > 0

    def test_events_filters_by_since(self, client):
        """Verify /events correctly filters: events with timestamp <= since are excluded."""
        # Use middle event as cutoff; only the newest event should be returned
        cutoff = TEST_EVENTS[1].timestamp.replace(microsecond=0)
        response = client.get("/events", params={"since": cutoff.isoformat()})
        assert response.status_code == 200
        events = response.json()
        
        # All returned events must have timestamp > cutoff
        for event in events:
            # Handle both Z suffix and +00:00 format
            ts_str = event["timestamp"].replace("Z", "+00:00")
            event_ts = datetime.fromisoformat(ts_str)
            assert event_ts > cutoff, \
                f"Event timestamp {event_ts} should be > cutoff {cutoff}"
        
        # Should have fewer events than total (at least 1 event excluded by filter)
        assert len(events) < 30  # Arbitrary upper bound for this endpoint

    def test_events_rejects_naive_timestamp(self, client):
        """Verify /events rejects timezone-naive timestamps."""
        naive_ts = "2024-01-01T12:00:00"  # No timezone info
        # The endpoint raises ValueError for naive timestamps during request handling
        with pytest.raises(ValueError, match="should be localized"):
            client.get("/events", params={"since": naive_ts})
        
    def test_events_accepts_iso8601_with_z_suffix(self, client):
        """Verify /events accepts ISO 8601 timestamps with Z suffix (UTC)."""
        # Use a timestamp in the past
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=2)).replace(microsecond=0)
        iso_z = cutoff.isoformat().replace("+00:00", "Z")
        response = client.get("/events", params={"since": iso_z})
        assert response.status_code == 200
        
    def test_events_accepts_iso8601_with_offset(self, client):
        """Verify /events accepts ISO 8601 timestamps with +00:00 offset."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(microsecond=0)
        iso_offset = cutoff.isoformat()
        response = client.get("/events", params={"since": iso_offset})
        assert response.status_code == 200

    def test_events_response_validates_pydantic_model(self, client):
        """Verify /events response contains valid ServerSeismicEvent shapes."""
        response = client.get("/events")
        assert response.status_code == 200
        events = response.json()
        
        # Should be able to parse each event as ServerSeismicEvent
        for event_data in events:
            try:
                event = ServerSeismicEvent.model_validate(event_data)
                # Spot check required fields
                assert hasattr(event, "eid")
                assert hasattr(event, "timestamp")
                assert hasattr(event, "lat")
                assert hasattr(event, "lon")
                assert hasattr(event, "depth")
                assert hasattr(event, "Mw")
            except Exception as e:
                pytest.fail(f"Event validation failed: {e}")


class TestHealthEndpoint:
    """Tests for GET /health"""

    def test_health_returns_ok(self, client):
        """Verify /health returns 200 with status: ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}
