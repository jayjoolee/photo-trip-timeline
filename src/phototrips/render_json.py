"""Render trips.json — the machine-facing contract for the Phase-2 LLM.

This file is gitignored (it carries coordinates and is derived from personal
photos). As a safety net we assert that no place/representative coordinate falls
inside the home radius before writing.
"""

from __future__ import annotations

from datetime import datetime

from .config import Config
from .geo import distance_from_home_km
from .home import HomeResult
from .model import PhotoPoint, Place, Trip
from .pipeline import PipelineResult
from .places import day_breakdown

SCHEMA_VERSION = "1.1"


class HomeCoordinateLeak(AssertionError):
    """Raised if an emitted coordinate falls inside the home radius."""


def build_json(
    result: PipelineResult,
    cfg: Config,
    photos_by_uuid: dict[str, PhotoPoint],
    generated_at: datetime,
) -> dict:
    doc = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at.isoformat(),
        "home_confidence": result.home.confidence,
        "filters": {"from_date": cfg.from_date.date().isoformat(), "movies": False},
        "trips": [_trip_dict(t, cfg, photos_by_uuid) for t in result.trips],
        "minor_trips": [_trip_dict(t, cfg, photos_by_uuid) for t in result.minor_trips],
    }
    _assert_no_home_coords(doc, result.home, cfg)
    return doc


def _trip_dict(t: Trip, cfg: Config, photos_by_uuid: dict[str, PhotoPoint]) -> dict:
    return {
        "trip_id": _trip_id(t),
        "title": t.title,
        "name_components": t.name_components,
        "date_start": t.date_start.isoformat(),
        "date_end": t.date_end.isoformat(),
        "duration_days": t.duration_days,
        "photo_count_total": t.photo_count_total,
        "photo_count_gps": t.photo_count_gps,
        "rescued": t.rescued,
        "place_sequence": [_place_dict(p, cfg) for p in t.places],
        "day_by_day": [
            {"day": d["day"], "date": d["date"].isoformat(),
             "places": d["places"], "photo_count": d["photo_count"]}
            for d in day_breakdown(t)
        ],
        "representative_photos": [
            _rep_dict(photos_by_uuid[u], cfg)
            for u in t.representative_uuids
            if u in photos_by_uuid
        ],
    }


def _place_dict(p: Place, cfg: Config) -> dict:
    d = {
        "place_name": p.label,
        "city": p.city,
        "photo_count": p.photo_count,
        "time_start": p.time_start.isoformat(),
        "time_end": p.time_end.isoformat(),
    }
    if not cfg.no_coords:
        d["lat"] = round(p.lat, 5)
        d["lon"] = round(p.lon, 5)
    return d


def _rep_dict(p: PhotoPoint, cfg: Config) -> dict:
    d = {
        "uuid": p.uuid,
        "time": p.dt.isoformat(),
        "place_name": p.area_of_interest or p.place_name or p.city,
        "score_overall": p.score,
        "is_favorite": p.favorite,
        "person_count": p.person_count,
        "people": p.persons if cfg.include_names else None,
        "caption_hint": ", ".join(x for x in (p.area_of_interest or p.place_name, p.city) if x),
    }
    if not cfg.no_coords and p.has_gps:
        d["lat"] = round(p.lat, 5)
        d["lon"] = round(p.lon, 5)
    return d


def _trip_id(t: Trip) -> str:
    anchor = (t.name_components.get("anchor_city") or "trip").lower().replace(" ", "-")
    return f"{t.date_start.date().isoformat()}-{anchor}"


def _assert_no_home_coords(doc: dict, home: HomeResult, cfg: Config) -> None:
    if cfg.no_coords or not home.windows:
        return
    for trip in doc["trips"] + doc["minor_trips"]:
        coords = [(p.get("lat"), p.get("lon")) for p in trip["place_sequence"]]
        coords += [(p.get("lat"), p.get("lon")) for p in trip["representative_photos"]]
        for lat, lon in coords:
            if lat is None or lon is None:
                continue
            for w in home.windows:
                if distance_from_home_km(lat, lon, (w.lat, w.lon)) * 1000.0 <= cfg.home_radius_m:
                    raise HomeCoordinateLeak(
                        f"coordinate {lat},{lon} falls inside the home radius"
                    )
