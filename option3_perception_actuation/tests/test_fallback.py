"""
Unit tests for listener.fallback module.

Tests:
- Agency selection (primary vs secondary)
- Failover trigger
- Recovery trigger
- State transitions
"""

import pytest
from listener.fallback import FallbackPolicy, AgencyState


@pytest.fixture
def policy():
    """Provide a FallbackPolicy instance."""
    return FallbackPolicy(primary_name="Agency A", secondary_name="Agency B")


class TestFallbackPolicy:
    """Tests for FallbackPolicy class."""

    def test_init_defaults_to_primary(self, policy):
        """should initialize with primary as active."""
        assert policy.pick_agency() == "Agency A"
        assert policy.is_primary_active() is True

    def test_pick_agency_returns_active(self, policy):
        """should return the currently active agency."""
        assert policy.pick_agency() == "Agency A"

    def test_on_failure_switches_to_secondary(self, policy):
        """should switch to secondary on primary failure."""
        policy.on_failure()
        assert policy.pick_agency() == "Agency B"
        assert policy.is_primary_active() is False

    def test_on_recovery_switches_back_to_primary(self, policy):
        """should switch back to primary on recovery."""
        policy.on_failure()
        assert policy.pick_agency() == "Agency B"
        
        policy.on_recovery()
        assert policy.pick_agency() == "Agency A"
        assert policy.is_primary_active() is True

    def test_on_failure_idempotent_when_already_secondary(self, policy):
        """should not raise error if already using secondary."""
        policy.on_failure()
        assert policy.pick_agency() == "Agency B"
        
        # Call again, should remain on secondary.
        policy.on_failure()
        assert policy.pick_agency() == "Agency B"

    def test_on_recovery_idempotent_when_already_primary(self, policy):
        """should not raise error if already using primary."""
        assert policy.pick_agency() == "Agency A"
        
        # Call recovery when already primary, should remain primary.
        policy.on_recovery()
        assert policy.pick_agency() == "Agency A"

    def test_failover_and_recovery_cycle(self, policy):
        """should handle multiple failover/recovery cycles."""
        # Start at primary.
        assert policy.pick_agency() == "Agency A"
        
        # Fail over to secondary.
        policy.on_failure()
        assert policy.pick_agency() == "Agency B"
        
        # Recover to primary.
        policy.on_recovery()
        assert policy.pick_agency() == "Agency A"
        
        # Fail over again.
        policy.on_failure()
        assert policy.pick_agency() == "Agency B"
        
        # Recover again.
        policy.on_recovery()
        assert policy.pick_agency() == "Agency A"
