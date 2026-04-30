from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

class ExternalServiceConfig(BaseModel):
    """Configuration for one seismic data agency endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., description="Human-readable name of the agency.")
    url: HttpUrl = Field(..., description="Base URL of the agency's API.")


class PullNowEndpoint(BaseModel):
    """Network binding for the on-demand pull endpoint exposed to the orchestrator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    host: str = Field(..., description="Host address.")
    port: int = Field(..., ge=1, le=65535, description="TCP port.")


class ListenerConfig(BaseModel):
    """Top-level configuration for the LISTENER service."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    pull_now_endpoint: PullNowEndpoint = Field(..., description="Where the on-demand pull endpoint binds.")

    poll_interval_minutes: int = Field(..., ge=1, alias="m", description="Polling interval in minutes.")
    lookback_window_minutes: int = Field(..., ge=1, description="Window of past events fetched per pull. Must exceed poll_interval_minutes.")
    liveness_threshold_minutes: int = Field(..., ge=1, description="System is marked degraded if no successful pull occurs within this window.")

    timeout_seconds: float = Field(..., gt=0.0, description="Per-request timeout for agency calls.")
    max_retries: int = Field(..., ge=0, description="Retries per agency call before triggering failover.")
    health_probe_interval_seconds: float = Field(..., gt=0.0, description="Interval at which the primary is probed during failover.")

    storage_path: str = Field(..., description="Path to the SQLite database file.")

    primary_service: ExternalServiceConfig = Field(..., description="Primary agency.")
    secondary_service: ExternalServiceConfig = Field(..., description="Fallback agency used when primary is unavailable.")

    @model_validator(mode="after")
    def _check_lookback_exceeds_interval(self) -> "ListenerConfig":
        if self.lookback_window_minutes <= self.poll_interval_minutes:
            raise ValueError(
                "lookback_window_minutes must exceed poll_interval_minutes "
                "to ensure pull windows overlap."
            )
        return self
    
def load_config(path: str) -> ListenerConfig:
    """Load and validate the listener configuration from a YAML file."""
    import yaml

    with open(path, "r") as f:
        raw = yaml.safe_load(f)
    return ListenerConfig.model_validate(raw["listener"])