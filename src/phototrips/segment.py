"""Trip segmentation: cut a time-ordered event stream into trips.

This is the core insight of the tool. Photos are sparse, so density clustering
can't find trip *boundaries* — we segment the timeline first, then cluster
places *within* each trip (see places.py).

A trip is time spent **away from home** — i.e. beyond ``away_km`` of the home
location. Photos near home (your home city / daily life) are NOT trips; they act
as boundaries that close an away-period. This is what stops everyday photos
around your own city from being reported as hundreds of tiny "trips."

Within a single away-period, we still cut a new trip when ANY fires:

  - away time gap: >= 48 h between consecutive away photos (drove/flew elsewhere
    after a quiet stretch, with no near-home photo in between)
  - fast spatial jump: >= 100 km within <= 12 h (a flight / long drive)
  - slow long-haul move: >= 200 km regardless of time (overland to a new region)
"""

from __future__ import annotations

from .config import Config
from .geo import distance_from_home_km, haversine_km
from .home import HomeResult
from .model import Event, Trip


def segment_trips(events: list[Event], home: HomeResult, cfg: Config) -> list[Trip]:
    """Split burst-collapsed events (UTC-ordered) into away-from-home trips.

    Only events farther than ``away_km`` from home are trip material. A
    near-home event closes the current away-period (you came back); the next
    away event starts a fresh trip.
    """
    runs: list[list[Event]] = []
    current: list[Event] = []
    prev_away: Event | None = None

    for e in events:
        h = home.for_date(e.dt)
        away = distance_from_home_km(e.lat, e.lon, h) > cfg.away_km

        if not away:
            # Back in the home region: close any open trip.
            if current:
                runs.append(current)
                current = []
            prev_away = None
            continue

        if current and prev_away is not None and _is_boundary(prev_away, e, cfg):
            runs.append(current)
            current = []

        current.append(e)
        prev_away = e

    if current:
        runs.append(current)

    trips = [_build_trip(r, home, cfg) for r in runs if r]
    return _demote_weak(trips, cfg)


def _is_boundary(prev: Event, cur: Event, cfg: Config) -> bool:
    """Boundary *within* a contiguous away-period (both events are away)."""
    dt_h = (cur.utc_instant - prev.utc_instant) / 3600.0
    dd_km = haversine_km(prev.lat, prev.lon, cur.lat, cur.lon)

    # Long quiet gap while still away -> distinct trips.
    if dt_h >= cfg.trip_gap_away_h:
        return True
    # Fast spatial jump (flight / long drive within a short window).
    if dd_km >= cfg.jump_km and dt_h <= cfg.jump_window_h:
        return True
    # Slow long-haul overland move to a different region.
    if dd_km >= cfg.longhaul_km:
        return True
    return False


def _build_trip(run: list[Event], home: HomeResult, cfg: Config) -> Trip:
    max_home_km = max(
        distance_from_home_km(e.lat, e.lon, home.for_date(e.dt)) for e in run
    )
    return Trip(events=run, home_distance_km=max_home_km)


def _demote_weak(trips: list[Trip], cfg: Config) -> list[Trip]:
    """Demote weak candidates to minor; rescue far-from-home ones with evidence.

    A single geotagged photo is treated as noise (a layover snap, a flight-path
    shot) and is always minor, no matter how far away — one photo can't be a
    trip. Otherwise a weak trip (few photos / short span) is rescued only when it
    is genuinely far from home.
    """
    for t in trips:
        if t.photo_count_gps < cfg.min_trip_photos:
            t.minor = True
            continue
        span_h = (t.date_end - t.date_start).total_seconds() / 3600.0
        weak = t.photo_count_gps < cfg.weak_min_photos or span_h < cfg.weak_min_hours
        if not weak:
            continue
        far = t.home_distance_km >= cfg.rescue_km
        if far:
            t.rescued = True  # distance from home is a strong "real trip" signal
        else:
            t.minor = True
    return trips
