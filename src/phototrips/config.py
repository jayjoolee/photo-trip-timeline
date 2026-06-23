"""All tunable parameters live here as one dataclass of defaults.

Defaults are research-backed (stay-point detection / spatiotemporal
segmentation literature) and chosen to match how a person remembers their own
trips rather than to optimize a clustering metric. Every value can be
overridden from the CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Config:
    # Time window
    from_date: datetime = datetime(2022, 7, 1)

    # Home / "on a trip" geometry
    home_radius_m: float = 300.0   # used for home detection + privacy assertions
    away_km: float = 50.0          # beyond this from home = "on a trip"

    # Trip-boundary thresholds (applied within a contiguous away-period)
    trip_gap_away_h: float = 48.0  # quiet gap that still splits two away trips
    jump_km: float = 100.0         # fast spatial jump distance...
    jump_window_h: float = 12.0    # ...within this time => boundary
    longhaul_km: float = 200.0     # slow overland move to a new region

    # Burst de-dup
    burst_min: float = 2.0         # minutes
    burst_m: float = 50.0          # meters

    # Within-trip place clustering (DBSCAN)
    place_eps_m: float = 300.0
    place_min_samples: int = 2

    # Weak-trip demotion / rescue
    min_trip_photos: int = 2       # a single geotag is noise, never a trip
    weak_min_photos: int = 3
    weak_min_hours: float = 2.0
    rescue_km: float = 100.0       # far-from-home trips survive even if weak

    # Naming
    aoi_coverage_min: float = 0.30  # use area-of-interest in name only above this

    # Representative photos
    rep_n: int = 5

    # Home night-window for the modal-cluster fallback (local hours)
    night_start_h: int = 22
    night_end_h: int = 7
    night_eps_m: float = 150.0
    home_dominance: float = 2.0    # winning cluster must beat runner-up by this
    home_min_nights: int = 3       # ...and have at least this many night points

    # Output
    lang: str = "en"               # timeline.md structural language: en | ko | zh

    # Privacy
    no_coords: bool = False        # if True, never emit any numeric coordinate
    include_names: bool = False    # opt-in person names into trips.json
