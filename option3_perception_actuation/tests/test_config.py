import pytest

from listener.config import ListenerConfig, load_config

def test_should_create_from_valid_config():
    """
    should successfully create a ListenerConfig instance from a valid config dictionary.
    """
    config_dict = {
        "pull_now_endpoint": {"host": "127.0.0.1", "port": 8000},
        "m": 5,
        "lookback_window_minutes": 10,
        "liveness_threshold_minutes": 15,
        "timeout_seconds": 30.0,
        "max_retries": 3,
        "health_probe_interval_seconds": 60.0,
        "storage_path": "/tmp/listener.db",
        "primary_service": {"name": "Primary", "url": "http://127.0.0.1:8001"},
        "secondary_service": {"name": "Secondary", "url": "http://127.0.0.1:8002"}
    }
    config = ListenerConfig.model_validate(config_dict)
    assert config.pull_now_endpoint.host == "127.0.0.1"
    assert config.pull_now_endpoint.port == 8000


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

VALID_CONFIG = {
    "pull_now_endpoint": {"host": "127.0.0.1", "port": 8000},
    "m": 5,
    "lookback_window_minutes": 10,
    "liveness_threshold_minutes": 15,
    "timeout_seconds": 30.0,
    "max_retries": 3,
    "health_probe_interval_seconds": 60.0,
    "storage_path": "/tmp/listener.db",
    "primary_service": {"name": "Primary", "url": "http://127.0.0.1:8001"},
    "secondary_service": {"name": "Secondary", "url": "http://127.0.0.1:8002"},
}


def _config_without(*keys: str) -> dict:
    return {k: v for k, v in VALID_CONFIG.items() if k not in keys}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing_field", list(VALID_CONFIG.keys()))
def test_fails_if_required_field_missing(missing_field: str):
    """should fail if any required field is absent."""
    with pytest.raises(Exception):
        ListenerConfig.model_validate(_config_without(missing_field))


def test_fails_if_extra_field_present():
    """should fail if an undeclared extra field is supplied."""
    data = {**VALID_CONFIG, "unexpected_field": "oops"}
    with pytest.raises(Exception):
        ListenerConfig.model_validate(data)


@pytest.mark.parametrize("m, lookback", [
    (5, 5),   # equal — not strictly greater
    (5, 4),   # lookback less than interval
    (5, 1),   # lookback much less than interval
])
def test_fails_if_lookback_does_not_exceed_interval(m: int, lookback: int):
    """should fail when lookback_window_minutes does not exceed poll_interval_minutes (m)."""
    data = {**VALID_CONFIG, "m": m, "lookback_window_minutes": lookback}
    with pytest.raises(Exception):
        ListenerConfig.model_validate(data)


def test_load_config_from_example_yaml():
    """should load and validate config.yaml without errors."""
    import pathlib

    config_path = pathlib.Path(__file__).parent / "fixtures" / "config.yaml"
    config = load_config(str(config_path))
    assert config.poll_interval_minutes == 1
    assert config.lookback_window_minutes == 5
    assert config.liveness_threshold_minutes == 10
    assert config.timeout_seconds == 5.0
    assert config.max_retries == 3
    assert config.health_probe_interval_seconds == 10.0
    assert config.storage_path == "./data/listener.db"
    assert config.primary_service.name == "Agency A"
    assert config.secondary_service.name == "Agency B"