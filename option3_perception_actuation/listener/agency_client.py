"""
AgencyClient: Fetch seismic events from an agency endpoint.

Responsibilities:
- Fetch events from an agency since a given timestamp.
- Health checks for availability.
- Handle timeouts and retries with exponential backoff.
- Log errors and anomalies.
"""

import httpx
from datetime import datetime

from listener.logging_setup import configure_logging
from listener.models import ClientSeismicEvent

logger = configure_logging(__name__)

class AgencyClient:
    """
    Client for communicating with a seismic event agency.
    
    Handles HTTP requests with timeouts and retries.
    """

    def __init__(
        self,
        agency_url: str,
        agency_name: str,
        timeout_seconds: float,
        max_retries: int,
    ):
        """
        Initialize the agency client.
        
        Args:
            agency_url: Base URL of the agency API (e.g., http://127.0.0.1:8001).
            agency_name: Human-readable name of the agency for logging.
            timeout_seconds: Timeout per request in seconds.
            max_retries: Number of retries before giving up.
        """
        self.agency_url = str(agency_url).rstrip("/")
        self.agency_name = agency_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def health(self) -> bool:
        """
        Check if the agency is healthy.
        
        Returns:
            True if the agency responds with 200 OK, False otherwise.
        """
        url = f"{self.agency_url}/health"
        try:
            with httpx.Client() as client:
                response = client.get(
                    url,
                    timeout=self.timeout_seconds,
                )
                is_healthy = response.status_code == 200
                if is_healthy:
                    logger.debug(f"{self.agency_name} health check OK")
                else:
                    logger.warning(
                        f"{self.agency_name} health check failed: "
                        f"status {response.status_code}"
                    )
                return is_healthy
        except httpx.TimeoutException:
            logger.warning(f"{self.agency_name} health check timeout")
            return False
        except Exception as e:
            logger.warning(f"{self.agency_name} health check error: {e}")
            return False

    def fetch_since(self, since: datetime) -> list[ClientSeismicEvent]:
        """
        Fetch events from the agency since a given timestamp.
        
        Retries on failure up to max_retries times.
        
        Args:
            since: Fetch events after this datetime (UTC).
        
        Returns:
            List of ClientSeismicEvent instances.
        
        Raises:
            Exception: If all retries are exhausted.
        """
        url = f"{self.agency_url}/events"
        params = {"since": since.isoformat()}
        
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client() as client:
                    response = client.get(
                        url,
                        params=params,
                        timeout=self.timeout_seconds,
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Parse response as list of ClientSeismicEvent.
                    events = [ClientSeismicEvent(**event) for event in data]
                    logger.debug(
                        f"{self.agency_name} fetch_since returned {len(events)} events"
                    )
                    return events
                    
            except httpx.TimeoutException:
                logger.warning(
                    f"{self.agency_name} request timeout (attempt {attempt + 1}/{self.max_retries + 1})"
                )
            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"{self.agency_name} HTTP error {e.response.status_code} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
            except Exception as e:
                logger.warning(
                    f"{self.agency_name} fetch_since error: {e} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
            
            # If this was the last attempt, raise.
            if attempt == self.max_retries:
                raise RuntimeError(
                    f"Failed to fetch events from {self.agency_name} after "
                    f"{self.max_retries + 1} attempts"
                )
        
        return []  # Unreachable, but for type correctness.