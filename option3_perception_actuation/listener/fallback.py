"""
FallbackPolicy: Manage primary/secondary agency switching.

Responsibilities:
- Pick the current active agency (primary by default, secondary on failover).
- Trigger failover when primary is unavailable.
- Check primary health periodically and recover when available.
"""

from enum import Enum
from listener.logging_setup import configure_logging

logger = configure_logging(__name__)


class AgencyState(Enum):
    """State of an agency."""
    PRIMARY = "primary"
    SECONDARY = "secondary"


class FallbackPolicy:
    """
    Manages agency selection and fallover/recovery logic.
    
    Selects primary by default. On primary failure, switches to secondary.
    Periodically checks primary health for recovery.
    """

    def __init__(self, primary_name: str, secondary_name: str):
        """
        Initialize the fallback policy.
        
        Args:
            primary_name: Name of the primary agency.
            secondary_name: Name of the secondary agency.
        """
        self.primary_name = primary_name
        self.secondary_name = secondary_name
        self._active_state = AgencyState.PRIMARY
        logger.info(f"FallbackPolicy initialized: primary={primary_name}, secondary={secondary_name}")

    def pick_agency(self) -> str:
        """
        Return the name of the currently active agency.
        
        Returns:
            Name of the agency to use for the next pull.
        """
        if self._active_state == AgencyState.PRIMARY:
            return self.primary_name
        else:
            return self.secondary_name

    def on_failure(self) -> None:
        """
        Mark primary as failed and switch to secondary.
        
        Logs the switch event at INFO level.
        """
        if self._active_state == AgencyState.PRIMARY:
            self._active_state = AgencyState.SECONDARY
            logger.info(f"agency switch: {self.primary_name} -> {self.secondary_name}")
        # else: already using secondary, no-op.

    def on_recovery(self) -> None:
        """
        Mark primary as recovered and switch back.
        
        Logs the recovery event at INFO level.
        """
        if self._active_state == AgencyState.SECONDARY:
            self._active_state = AgencyState.PRIMARY
            logger.info(f"agency recovered: {self.secondary_name} -> {self.primary_name}")
        # else: already using primary, no-op.

    def is_primary_active(self) -> bool:
        """
        Check if primary agency is currently active.
        
        Returns:
            True if primary is active, False if secondary is active.
        """
        return self._active_state == AgencyState.PRIMARY