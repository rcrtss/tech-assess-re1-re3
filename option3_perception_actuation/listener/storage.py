"""
EventStore: Persistence layer for seismic events via SQLite.

Responsibilities:
- Initialize and manage a SQLite database schema for seismic events.
- Provide methods to add validated events (with dedup via UNIQUE + INSERT OR IGNORE).
- Check event existence by eid.
- Retrieve recent events.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from listener.logging_setup import configure_logging
from listener.models import ClientSeismicEvent

logger = configure_logging(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
    eid INTEGER PRIMARY KEY UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    depth REAL NOT NULL,
    Mw REAL NOT NULL,
    dist REAL NOT NULL,
    azi REAL NOT NULL,
    loclat REAL NOT NULL,
    loclon REAL NOT NULL,
    stored_at TEXT NOT NULL
);
"""


class EventStore:
    """
    Manages persistence of seismic events to SQLite.
    
    Deduplication is handled at the database level via UNIQUE constraint on eid
    and INSERT OR IGNORE semantics.
    """

    def __init__(self, db_path: str):
        """
        Initialize the event store with a SQLite database.
        
        Args:
            db_path: Path to the SQLite database file.
        
        Raises:
            OSError: If the database cannot be opened or initialized.
        """
        self.db_path = db_path
        
        # Ensure parent directory exists.
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute(SCHEMA_SQL)
            self._conn.commit()
            logger.info(f"EventStore initialized at {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize EventStore: {e}")
            raise

    def add(self, event: ClientSeismicEvent) -> bool:
        """
        Add a seismic event to the store.
        
        Uses INSERT OR IGNORE to silently skip duplicates (same eid).
        
        Args:
            event: ClientSeismicEvent instance.
        
        Returns:
            True if the event was inserted, False if it was a duplicate.
        """
        try:
            cursor = self._conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                """
                INSERT OR IGNORE INTO events (
                    eid, timestamp, lat, lon, depth, Mw, dist, azi, loclat, loclon, stored_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.eid,
                    event.timestamp.isoformat(),
                    event.lat,
                    event.lon,
                    event.depth,
                    event.Mw,
                    event.dist,
                    event.azi,
                    event.loclat,
                    event.loclon,
                    now,
                ),
            )
            self._conn.commit()
            inserted = cursor.rowcount > 0
            if inserted:
                logger.debug(f"Event {event.eid} inserted")
            else:
                logger.debug(f"Event {event.eid} already exists (dedup)")
            return inserted
        except Exception as e:
            logger.error(f"Failed to add event {event.eid}: {e}")
            raise

    def exists(self, eid: int) -> bool:
        """
        Check if an event with the given eid exists.
        
        Args:
            eid: Event ID.
        
        Returns:
            True if the event exists, False otherwise.
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT 1 FROM events WHERE eid = ? LIMIT 1", (eid,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check event existence for eid {eid}: {e}")
            raise

    def recent(self, n: int) -> list[ClientSeismicEvent]:
        """
        Retrieve the n most recent events, ordered by timestamp descending.
        
        Args:
            n: Number of events to retrieve.
        
        Returns:
            List of ClientSeismicEvent instances.
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT eid, timestamp, lat, lon, depth, Mw, dist, azi, loclat, loclon
                FROM events
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (n,),
            )
            rows = cursor.fetchall()
            events = []
            for row in rows:
                event = ClientSeismicEvent(
                    eid=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    lat=row[2],
                    lon=row[3],
                    depth=row[4],
                    Mw=row[5],
                    dist=row[6],
                    azi=row[7],
                    loclat=row[8],
                    loclon=row[9],
                )
                events.append(event)
            return events
        except Exception as e:
            logger.error(f"Failed to retrieve recent events: {e}")
            raise

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            logger.info("EventStore connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()