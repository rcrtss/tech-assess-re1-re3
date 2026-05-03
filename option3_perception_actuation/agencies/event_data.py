from datetime import datetime, timedelta, timezone

from agencies.models import ServerSeismicEvent

TIMELINE_START = datetime.now(timezone.utc)
EVENT_RELEASE_SECONDS = 3

_EVENT_SPECS = [
    dict(eid=1001, lat=37.5, lon=-3.6, depth=-8.0, Mw=4.2, dist=120.5, azi=45.0, loclat=40.0, loclon=-3.7),
    dict(eid=1002, lat=38.1, lon=-1.9, depth=-12.0, Mw=3.7, dist=85.0, azi=60.0, loclat=39.0, loclon=-2.0),
    dict(eid=1003, lat=36.8, lon=-4.1, depth=-5.0, Mw=2.9, dist=200.0, azi=-30.0, loclat=38.5, loclon=-4.0),
    dict(eid=1004, lat=39.5, lon=-0.4, depth=-20.0, Mw=5.1, dist=310.0, azi=90.0, loclat=40.4, loclon=-3.7),
    dict(eid=1005, lat=37.0, lon=-2.5, depth=-35.0, Mw=3.3, dist=145.0, azi=120.0, loclat=38.2, loclon=-2.8),
    dict(eid=1006, lat=40.1, lon=-5.2, depth=-8.5, Mw=4.8, dist=265.0, azi=-75.0, loclat=40.0, loclon=-3.7),
    dict(eid=1007, lat=36.3, lon=-6.0, depth=-15.0, Mw=3.1, dist=420.0, azi=-110.0, loclat=37.8, loclon=-4.5),
    dict(eid=1008, lat=38.7, lon=-3.0, depth=-50.0, Mw=6.0, dist=180.0, azi=15.0, loclat=40.0, loclon=-3.7),
    dict(eid=1009, lat=37.9, lon=-1.2, depth=-10.0, Mw=2.5, dist=95.0, azi=75.0, loclat=38.9, loclon=-1.5),
    dict(eid=1010, lat=41.2, lon=-2.8, depth=-30.0, Mw=4.4, dist=130.0, azi=-45.0, loclat=40.4, loclon=-3.7),
    dict(eid=1011, lat=36.5, lon=-5.5, depth=-7.0, Mw=3.9, dist=380.0, azi=-95.0, loclat=39.0, loclon=-4.0),
    dict(eid=1012, lat=39.8, lon=-1.5, depth=-18.0, Mw=5.5, dist=225.0, azi=55.0, loclat=40.0, loclon=-3.7),
    dict(eid=1013, lat=37.3, lon=-4.8, depth=-25.0, Mw=2.7, dist=155.0, azi=-20.0, loclat=38.0, loclon=-4.5),
    dict(eid=1014, lat=40.6, lon=-4.5, depth=-60.0, Mw=4.1, dist=100.0, azi=-60.0, loclat=40.4, loclon=-3.7),
    dict(eid=1015, lat=38.4, lon=-0.8, depth=-9.0, Mw=3.6, dist=275.0, azi=100.0, loclat=39.5, loclon=-1.5),
    dict(eid=1016, lat=36.0, lon=-3.3, depth=-14.0, Mw=5.8, dist=340.0, azi=-5.0, loclat=38.0, loclon=-3.5),
    dict(eid=1017, lat=39.2, lon=-6.1, depth=-22.0, Mw=3.0, dist=490.0, azi=-130.0, loclat=40.0, loclon=-3.7),
    dict(eid=1018, lat=37.7, lon=-2.1, depth=-40.0, Mw=4.6, dist=160.0, azi=35.0, loclat=38.5, loclon=-2.5),
    dict(eid=1019, lat=40.9, lon=-3.9, depth=-5.5, Mw=2.3, dist=115.0, azi=-80.0, loclat=40.4, loclon=-3.7),
    dict(eid=1020, lat=38.0, lon=-5.0, depth=-28.0, Mw=5.3, dist=290.0, azi=-50.0, loclat=39.0, loclon=-4.0),
    dict(eid=1021, lat=37.1, lon=-1.0, depth=-11.0, Mw=3.4, dist=210.0, azi=80.0, loclat=38.0, loclon=-2.0),
    dict(eid=1022, lat=39.6, lon=-2.3, depth=-45.0, Mw=4.9, dist=170.0, azi=10.0, loclat=40.0, loclon=-3.7),
]


def _build_timeline() -> list[ServerSeismicEvent]:
    events: list[ServerSeismicEvent] = []
    for index, spec in enumerate(_EVENT_SPECS):
        event_time = TIMELINE_START + timedelta(seconds=index * EVENT_RELEASE_SECONDS)
        events.append(ServerSeismicEvent(timestamp=event_time, **spec))
    return events


# Immutable event history for each running agency process.
EVENTS: list[ServerSeismicEvent] = _build_timeline()


def get_available_events(now: datetime | None = None) -> list[ServerSeismicEvent]:
    """Return only the events that have occurred so far in the simulated timeline."""
    current_time = now or datetime.now(timezone.utc)
    return [event for event in EVENTS if event.timestamp <= current_time]