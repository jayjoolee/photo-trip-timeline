"""Within-trip place clustering and timeline simplification.

Within a single trip the photo points are dense and bounded, so DBSCAN finds
the distinct places visited. Places are ordered by first-photo time to form the
trip's route. For the human-readable timeline we additionally *simplify*:
consecutive places sharing a label collapse into one named segment, so a long
walk through one neighborhood reads as one stop, not five.
"""

from __future__ import annotations

from collections import Counter

from .config import Config
from .geo import dbscan
from .model import Event, Place, Trip


def build_places(trip: Trip, cfg: Config) -> list[Place]:
    """Cluster a trip's events into the distinct places visited, time-ordered."""
    events = trip.events
    coords = [(e.lat, e.lon) for e in events]
    labels = dbscan(coords, cfg.place_eps_m, cfg.place_min_samples)

    # Group events by cluster label; noise points (-1) each become their own
    # singleton place so nothing visited is dropped from the route.
    groups: dict[int, list[Event]] = {}
    singleton = -1000
    for ev, lab in zip(events, labels):
        key = lab if lab != -1 else (singleton := singleton - 1)
        groups.setdefault(key, []).append(ev)

    places = []
    for evs in groups.values():
        place = _place_from_events(evs)
        for ev in evs:  # tag events so day-by-day can bucket by real photo time
            ev.place_label = place.label
        places.append(place)
    places.sort(key=lambda p: p.time_start)
    trip.places = places
    return places


def _place_from_events(events: list[Event]) -> Place:
    photos = [m for e in events for m in e.members]
    lat = sum(e.lat for e in events) / len(events)
    lon = sum(e.lon for e in events) / len(events)
    return Place(
        label=_label_for(photos),
        city=_modal(p.city for p in photos),
        lat=lat,
        lon=lon,
        photo_count=len(photos),
        time_start=min(e.dt for e in events),
        time_end=max(e.dt for e in events),
        member_uuids=[p.uuid for p in photos],
    )


def _label_for(photos) -> str:
    """Prefer Apple's area-of-interest, then place name, then city."""
    for getter in (lambda p: p.area_of_interest, lambda p: p.place_name, lambda p: p.city):
        label = _modal(getter(p) for p in photos)
        if label:
            return label
    return "Unknown"


def _modal(values) -> str | None:
    counts = Counter(v for v in values if v)
    return counts.most_common(1)[0][0] if counts else None


def simplify_sequence(places: list[Place]) -> list[Place]:
    """Collapse consecutive same-label places into one segment for the timeline.

    Returns new merged Place objects; the trip's fine-grained ``places`` list is
    left intact for trips.json (the LLM phase wants the detail).
    """
    if not places:
        return []
    merged: list[Place] = [_copy_place(places[0])]
    for p in places[1:]:
        last = merged[-1]
        if p.label == last.label:
            last.photo_count += p.photo_count
            last.time_end = max(last.time_end, p.time_end)
            last.member_uuids = last.member_uuids + p.member_uuids
        else:
            merged.append(_copy_place(p))
    return merged


def day_breakdown(trip: Trip) -> list[dict]:
    """Per-day breakdown bucketed by actual photo timestamps.

    Days are ordinal (1, 2, 3...) relative to the trip's calendar days, so a
    place revisited on multiple days is counted on each day it was photographed
    — not collapsed into the day its cluster happened to start.
    """
    buckets: dict = {}
    for ev in trip.events:  # already UTC-ordered
        d = ev.dt.date()
        b = buckets.setdefault(d, {"labels": [], "photo_count": 0})
        b["photo_count"] += ev.photo_count
        label = ev.place_label or "Unknown"
        if label not in b["labels"]:
            b["labels"].append(label)

    # GPS-less photos assigned to this trip count toward their day's total but
    # carry no place (we don't know where they were taken).
    for p in trip.no_gps_points:
        b = buckets.setdefault(p.dt.date(), {"labels": [], "photo_count": 0})
        b["photo_count"] += 1

    out = []
    for i, d in enumerate(sorted(buckets), start=1):
        b = buckets[d]
        out.append({
            "day": i,
            "date": d,
            "places": b["labels"],
            "photo_count": b["photo_count"],
        })
    return out


def _copy_place(p: Place) -> Place:
    return Place(
        label=p.label,
        city=p.city,
        lat=p.lat,
        lon=p.lon,
        photo_count=p.photo_count,
        time_start=p.time_start,
        time_end=p.time_end,
        member_uuids=list(p.member_uuids),
    )
