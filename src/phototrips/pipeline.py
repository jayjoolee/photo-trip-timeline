"""End-to-end algorithm pipeline over normalized PhotoPoints.

Kept separate from extract.py/cli.py so the whole thing can run on synthetic
fixtures in CI without a Photos library. Input is plain PhotoPoints; output is
fully-populated Trip objects plus the resolved home.
"""

from __future__ import annotations

from dataclasses import dataclass

from .assign import assign_no_gps
from .config import Config
from .dedupe import collapse_bursts
from .home import HomeResult, HomeWindow, detect_home
from .model import PhotoPoint, Trip
from .naming import name_trip
from .places import build_places
from .represent import select_representatives
from .segment import segment_trips


@dataclass
class PipelineResult:
    trips: list[Trip]          # significant trips
    minor_trips: list[Trip]    # demoted near-home weak candidates
    home: HomeResult


def _on_or_after(dt, ref) -> bool:
    """Compare a (possibly tz-aware) photo time against a naive local cutoff.

    osxphotos returns tz-aware datetimes; the ``--since`` cutoff is a naive
    local date. Comparing the photo's wall-clock time matches what a user means
    by "photos since 2022-07-01".
    """
    wall = dt.replace(tzinfo=None) if dt.tzinfo is not None else dt
    return wall >= ref


def run_pipeline(
    points: list[PhotoPoint],
    cfg: Config,
    user_homes: list[HomeWindow] | None = None,
) -> PipelineResult:
    in_window = [p for p in points if _on_or_after(p.dt, cfg.from_date)]
    gps = sorted((p for p in in_window if p.has_gps), key=lambda p: p.utc_instant)
    no_gps = [p for p in in_window if not p.has_gps]

    home = detect_home(gps, cfg, user_homes)

    events = collapse_bursts(gps, cfg)
    all_trips = segment_trips(events, home, cfg)

    photos_by_uuid = {p.uuid: p for p in gps}
    for t in all_trips:
        build_places(t, cfg)
        t.title, t.name_components = name_trip(t, cfg)
        select_representatives(t, photos_by_uuid, cfg)

    significant = [t for t in all_trips if not t.minor]
    minor = [t for t in all_trips if t.minor]

    # GPS-less photos only inflate counts for real trips, not minor blips.
    assign_no_gps(significant, no_gps)

    significant.sort(key=lambda t: t.date_start, reverse=True)
    minor.sort(key=lambda t: t.date_start, reverse=True)
    return PipelineResult(trips=significant, minor_trips=minor, home=home)
