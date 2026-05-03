from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ClientSeismicEvent(BaseModel):
    """
    Represents a seismic event reported by the server. In this case the model is exactly the same as
    the agent's ServerSeismicEvent, but in a real application these naturally could differ. Each
    service owns its own data models even if they should match for correct operation.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    eid: int = Field(..., ge=0, description="Unique event identifier (natural number).")
    timestamp: datetime = Field(..., description="UTC timestamp of the seismic event.")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Hypocenter latitude in degrees [-90, +90].")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Hypocenter longitude in degrees [-180, +180].")
    depth: float = Field(..., ge=-100.0, le=0.0, description="Hypocenter depth in km [-100, 0]; negative values indicate depth below surface.")
    Mw: float = Field(..., ge=0.0, le=9.0, description="Moment magnitude of the earthquake [0.0, 9.0].")
    dist: float = Field(..., gt=0.0, description="Distance from the reference surface location to the hypocenter (positive real, km).")
    azi: float = Field(..., ge=-180.0, le=180.0, description="Azimuth from the reference location to the hypocenter in degrees [-180, +180].")
    loclat: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the reference surface location in degrees [-90, +90].")
    loclon: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the reference surface location in degrees [-180, +180].")

    @field_validator("timestamp")
    @classmethod
    def _ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (UTC)")
        return v.astimezone(timezone.utc)
    
    