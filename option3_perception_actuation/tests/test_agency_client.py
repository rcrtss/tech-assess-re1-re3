"""
Unit tests for listener.agency_client module.

Tests:
- Fetching events since a timestamp
- Health check endpoint
- Timeout handling
- Retry exhaustion
"""

import pytest
import httpx
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from listener.agency_client import AgencyClient
from listener.models import ClientSeismicEvent


@pytest.fixture
def sample_events_json():
    """Provide sample event JSON responses."""
    return [
        {
            "eid": 1,
            "timestamp": "2024-05-03T12:00:00+00:00",
            "lat": 35.5,
            "lon": 139.8,
            "depth": -10.5,
            "Mw": 5.2,
            "dist": 100.0,
            "azi": 45.0,
            "loclat": 36.0,
            "loclon": 140.0,
        },
        {
            "eid": 2,
            "timestamp": "2024-05-03T12:10:00+00:00",
            "lat": 36.0,
            "lon": 140.0,
            "depth": -15.0,
            "Mw": 4.8,
            "dist": 120.0,
            "azi": 60.0,
            "loclat": 36.5,
            "loclon": 140.5,
        },
    ]


@pytest.fixture
def agency_client():
    """Provide an AgencyClient instance."""
    return AgencyClient(
        agency_url="http://127.0.0.1:8001",
        agency_name="Agency A",
        timeout_seconds=5.0,
        max_retries=2,
    )


class TestAgencyClient:
    """Tests for AgencyClient class."""

    def test_health_returns_true_on_200(self, agency_client):
        """should return True when health endpoint returns 200."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            result = agency_client.health()
            assert result is True

    def test_health_returns_false_on_non_200(self, agency_client):
        """should return False when health endpoint does not return 200."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.status_code = 503
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            result = agency_client.health()
            assert result is False

    def test_health_returns_false_on_timeout(self, agency_client):
        """should return False when health check times out."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.TimeoutException("timeout")
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            result = agency_client.health()
            assert result is False

    def test_health_returns_false_on_exception(self, agency_client):
        """should return False on any exception."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.side_effect = Exception("connection error")
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            result = agency_client.health()
            assert result is False

    def test_fetch_since_returns_events(self, agency_client, sample_events_json):
        """should return parsed events on successful fetch."""
        since = datetime(2024, 5, 3, 11, 0, 0, tzinfo=timezone.utc)
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.json.return_value = sample_events_json
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            events = agency_client.fetch_since(since)
            assert len(events) == 2
            assert events[0].eid == 1
            assert events[1].eid == 2
            assert isinstance(events[0], ClientSeismicEvent)

    def test_fetch_since_raises_on_timeout(self, agency_client):
        """should raise after max retries due to timeout."""
        since = datetime(2024, 5, 3, 11, 0, 0, tzinfo=timezone.utc)
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.TimeoutException("timeout")
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            with pytest.raises(RuntimeError, match="Failed to fetch events"):
                agency_client.fetch_since(since)

    def test_fetch_since_raises_on_http_error(self, agency_client):
        """should raise after max retries due to HTTP error."""
        since = datetime(2024, 5, 3, 11, 0, 0, tzinfo=timezone.utc)
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_request = Mock()
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "error", request=mock_request, response=mock_response
            )
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            with pytest.raises(RuntimeError, match="Failed to fetch events"):
                agency_client.fetch_since(since)

    def test_fetch_since_raises_on_generic_exception(self, agency_client):
        """should raise after max retries due to generic exception."""
        since = datetime(2024, 5, 3, 11, 0, 0, tzinfo=timezone.utc)
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.side_effect = ValueError("invalid data")
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            with pytest.raises(RuntimeError, match="Failed to fetch events"):
                agency_client.fetch_since(since)

    def test_fetch_since_retries_on_failure(self, agency_client, sample_events_json):
        """should retry fetch_since on failure and succeed on later attempt."""
        since = datetime(2024, 5, 3, 11, 0, 0, tzinfo=timezone.utc)
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response_fail = Mock()
            mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
                "error",
                request=Mock(),
                response=Mock(status_code=500),
            )
            mock_response_success = Mock()
            mock_response_success.json.return_value = sample_events_json
            
            # First two calls fail, third succeeds.
            mock_client.get.side_effect = [
                mock_response_fail,
                mock_response_fail,
                mock_response_success,
            ]
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            events = agency_client.fetch_since(since)
            assert len(events) == 2
            assert events[0].eid == 1

    def test_fetch_since_includes_since_parameter(self, agency_client, sample_events_json):
        """should include 'since' timestamp in request params."""
        since = datetime(2024, 5, 3, 11, 0, 0, tzinfo=timezone.utc)
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.json.return_value = sample_events_json
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            agency_client.fetch_since(since)
            
            # Verify the params were passed correctly.
            mock_client.get.assert_called_once()
            call_kwargs = mock_client.get.call_args[1]
            assert "params" in call_kwargs
            assert call_kwargs["params"]["since"] == since.isoformat()

    def test_fetch_since_uses_configured_timeout(self, agency_client, sample_events_json):
        """should use configured timeout."""
        since = datetime(2024, 5, 3, 11, 0, 0, tzinfo=timezone.utc)
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.json.return_value = sample_events_json
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            agency_client.fetch_since(since)
            
            # Verify timeout was used.
            call_kwargs = mock_client.get.call_args[1]
            assert call_kwargs["timeout"] == agency_client.timeout_seconds

    def test_max_retries_is_respected(self, agency_client):
        """should attempt max_retries + 1 times before raising."""
        since = datetime(2024, 5, 3, 11, 0, 0, tzinfo=timezone.utc)
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.TimeoutException("timeout")
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            with pytest.raises(RuntimeError):
                agency_client.fetch_since(since)
            
            # Should have been called max_retries + 1 times.
            assert mock_client.get.call_count == agency_client.max_retries + 1

    def test_health_uses_configured_timeout(self, agency_client):
        """should use configured timeout for health check."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            agency_client.health()
            
            # Verify timeout was used.
            call_kwargs = mock_client.get.call_args[1]
            assert call_kwargs["timeout"] == agency_client.timeout_seconds

    def test_fetch_since_returns_empty_on_empty_response(self, agency_client):
        """should return empty list when agency returns empty list."""
        since = datetime(2024, 5, 3, 11, 0, 0, tzinfo=timezone.utc)
        
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            events = agency_client.fetch_since(since)
            assert events == []
