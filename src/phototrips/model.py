"""Core data structures shared across the pipeline.

Everything downstream of extraction operates on these plain dataclasses, so the
algorithm core can be exercised in tests with synthetic data and never needs a
real Photos library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PhotoPoint:
    """A single photo, normalized out of osxphotos (or a test fixture).

    ``dt`` is timezone-aware local time. ``tzoffset`` is seconds east of UTC,
    kept separately so we can order globally by UTC instant while still
    displaying and day-bucketing in the photo's own local time.
    """

    uuid: str
    dt: datetime
    lat: float | None = None
    lon: float | None = None
    tzoffset: int = 0
    place_name: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    country_code: str | None = None
    area_of_interest: str | None = None
    ishome: bool = False
    score: float | None = None
    favorite: bool = False
    person_count: int = 0
    persons: list[str] = field(default_factory=list)
    path: str | None = None

    @property
    def has_gps(self) -> bool:
        return self.lat is not None and self.lon is not None

    @property
    def utc_instant(self) -> float:
        """Global ordering / time-delta key in seconds since the epoch (UTC).

        For a timezone-aware datetime (what osxphotos returns) ``.timestamp()``
        is already the correct UTC instant, so two photos taken in different
        timezones on the same trip compare correctly. Naive fixtures fall back
        to the system-local interpretation, which is internally consistent.
        """
        return self.dt.timestamp()


@dataclass
class Event:
    """A burst-collapsed group of photos at essentially one place and instant."""

    members: list[PhotoPoint]
    place_label: str | None = None  # set during within-trip place clustering

    @property
    def representative(self) -> PhotoPoint:
        scored = [p for p in self.members if p.score is not None]
        if scored:
            return max(scored, key=lambda p: p.score)
        return self.members[0]

    @property
    def dt(self) -> datetime:
        return self.representative.dt

    @property
    def lat(self) -> float | None:
        return self.representative.lat

    @property
    def lon(self) -> float | None:
        return self.representative.lon

    @property
    def utc_instant(self) -> float:
        return self.representative.utc_instant

    @property
    def photo_count(self) -> int:
        return len(self.members)


@dataclass
class Place:
    """A distinct location visited within a trip (a within-trip DBSCAN cluster)."""

    label: str
    city: str | None
    lat: float
    lon: float
    photo_count: int
    time_start: datetime
    time_end: datetime
    member_uuids: list[str] = field(default_factory=list)


@dataclass
class Trip:
    events: list[Event]
    home_distance_km: float = 0.0  # max distance from home, set during segmentation
    rescued: bool = False
    minor: bool = False

    # Filled in by later stages:
    title: str = ""
    name_components: dict = field(default_factory=dict)
    places: list[Place] = field(default_factory=list)
    representative_uuids: list[str] = field(default_factory=list)
    no_gps_points: list[PhotoPoint] = field(default_factory=list)  # attached post-hoc

    @property
    def assigned_no_gps(self) -> int:
        return len(self.no_gps_points)

    @property
    def date_start(self) -> datetime:
        return min(e.dt for e in self.events)

    @property
    def date_end(self) -> datetime:
        return max(e.dt for e in self.events)

    @property
    def duration_days(self) -> int:
        return (self.date_end.date() - self.date_start.date()).days + 1

    @property
    def photo_count_gps(self) -> int:
        return sum(e.photo_count for e in self.events)

    @property
    def photo_count_total(self) -> int:
        return self.photo_count_gps + self.assigned_no_gps
