import pytest

from agencies.models import ServerSeismicEvent
from datetime import datetime, timezone
from pydantic import ValidationError

    
@pytest.mark.parametrize("field,invalid_value", [
    ("eid",       -1),              # negative event ID
    ("timestamp", "not-a-datetime"),# unparseable timestamp
    ("lat",       100.0),           # latitude out of range
    ("lon",       -200.0),          # longitude out of range
    ("depth",     -150.0),          # depth out of range
    ("Mw",        10.0),            # magnitude out of range
    ("dist",      -5.0),            # distance must be positive
    ("azi",       -190.0),          # azimuth out of range
    ("loclat",    95.0),            # location latitude out of range
    ("loclon",    -190.0),          # location longitude out of range
])
def test_should_fail_with_invalid_seismic_event_data(field, invalid_value):
    """
    should fail to create a ServerSeismicEvent instance if any single field is invalid.
    Each case starts from a fully valid dict and overrides exactly one field.
    """
    valid_base = {
        "eid":       12345,
        "timestamp": datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        "lat":       37.5,
        "lon":       -3.6,
        "depth":     -8.0,
        "Mw":        4.2,
        "dist":      120.5,
        "azi":       45.0,
        "loclat":    40.0,
        "loclon":    -3.7,
    }
    valid_base[field] = invalid_value

    with pytest.raises(ValidationError):
        ServerSeismicEvent.model_validate(valid_base)
    
def test_should_pass_with_valid_seismic_event_data():
    """
    should successfully create a ServerSeismicEvent instance from valid event data.
    """
    timestamp_value = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    event_data_dict = {
        "eid": 12345,
        "timestamp": timestamp_value,
        "lat": 37.5,
        "lon": -3.6,
        "depth": -8.0,
        "Mw": 4.2,
        "dist": 120.5,
        "azi": 45.0,
        "loclat": 40.0,
        "loclon": -3.7
    }
    event_data = ServerSeismicEvent.model_validate(event_data_dict)
    assert event_data.eid == 12345
    assert event_data.timestamp == timestamp_value
    assert event_data.lat == 37.5
    assert event_data.lon == -3.6
    assert event_data.depth == -8.0
    assert event_data.Mw == 4.2
    assert event_data.dist == 120.5
    assert event_data.azi == 45.0
    assert event_data.loclat == 40.0
    assert event_data.loclon == -3.7
    
def test_should_pass_if_dummy_events_valid():
    """
    should pass if all dummy events in agencies/event_data.py can be successfully validated as ServerSeismicEvent instances.
    This serves as a sanity check that the validation logic is correctly applied to the hardcoded dummy
    """
    from agencies.event_data import EVENTS
    for event in EVENTS:
        event_dict = event.model_dump()
        event = ServerSeismicEvent.model_validate(event_dict)
        assert isinstance(event, ServerSeismicEvent)

def test_should_pass_if_dummy_events_have_valid_timestamps():
    """
    should pass if all dummy events in agencies/event_data.py have timestamps that are timezone-aware and in UTC.
    This ensures that the field validator for timestamp is correctly applied to the hardcoded dummy events.
    """
    from agencies.event_data import EVENTS
    for event in EVENTS:
        assert event.timestamp.tzinfo is not None
        assert event.timestamp.tzinfo.utcoffset(event.timestamp) == timezone.utc.utcoffset(event.timestamp)
