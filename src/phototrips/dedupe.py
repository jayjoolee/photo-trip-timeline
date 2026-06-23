"""Burst de-duplication: collapse rapid-fire same-place photos into one event.

Runs before segmentation and clustering so an over-photographed sunset (20 near
identical frames) can't drag a place centroid or inflate boundary signals.
"""

from __future__ import annotations

from .config import Config
from .geo import haversine_m
from .model import Event, PhotoPoint


def collapse_bursts(points: list[PhotoPoint], cfg: Config) -> list[Event]:
    """Group consecutive GPS photos within burst_min minutes AND burst_m meters.

    ``points`` must already be sorted by UTC instant and contain only GPS photos.
    """
    events: list[Event] = []
    current: list[PhotoPoint] = []
    gap_s = cfg.burst_min * 60.0

    for p in points:
        if not current:
            current = [p]
            continue
        prev = current[-1]
        close_in_time = (p.utc_instant - prev.utc_instant) <= gap_s
        close_in_space = haversine_m(prev.lat, prev.lon, p.lat, p.lon) <= cfg.burst_m
        if close_in_time and close_in_space:
            current.append(p)
        else:
            events.append(Event(members=current))
            current = [p]

    if current:
        events.append(Event(members=current))
    return events
