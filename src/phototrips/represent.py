"""Representative-photo selection for a trip.

Goal: a small set that *covers* the trip geographically rather than N near-dupes
from the single most photogenic spot. We pick the best photo per place first
(spatial spread), then fill up to rep_n from the most-photographed places.

Quality signal is Apple's on-device aesthetic score (``score.overall``), with a
graceful order when it is missing (Photos < 5): favorite, then most people,
then the median-time shot.
"""

from __future__ import annotations

from statistics import median

from .config import Config
from .model import Place, PhotoPoint, Trip


def select_representatives(
    trip: Trip, photos_by_uuid: dict[str, PhotoPoint], cfg: Config
) -> list[str]:
    if not trip.places:
        return []

    # Best photo per place => guaranteed spatial coverage.
    chosen: list[str] = []
    for place in sorted(trip.places, key=lambda p: -p.photo_count):
        candidates = [photos_by_uuid[u] for u in place.member_uuids if u in photos_by_uuid]
        best = _best_photo(candidates)
        if best is not None and best.uuid not in chosen:
            chosen.append(best.uuid)
        if len(chosen) >= cfg.rep_n:
            break

    # If we still have room (fewer places than rep_n), add the next-best photos
    # from the most-photographed places.
    if len(chosen) < cfg.rep_n:
        pool = [
            photos_by_uuid[u]
            for place in sorted(trip.places, key=lambda p: -p.photo_count)
            for u in place.member_uuids
            if u in photos_by_uuid and u not in chosen
        ]
        for p in _rank_photos(pool):
            if p.uuid not in chosen:
                chosen.append(p.uuid)
            if len(chosen) >= cfg.rep_n:
                break

    trip.representative_uuids = chosen
    return chosen


def _best_photo(photos: list[PhotoPoint]) -> PhotoPoint | None:
    ranked = _rank_photos(photos)
    return ranked[0] if ranked else None


def _rank_photos(photos: list[PhotoPoint]) -> list[PhotoPoint]:
    if not photos:
        return []
    scored = [p for p in photos if p.score is not None]
    if scored:
        return sorted(scored, key=lambda p: p.score, reverse=True) + [
            p for p in photos if p.score is None
        ]
    # No aesthetic scores available: favorite, then most people, then median time.
    favs = [p for p in photos if p.favorite]
    if favs:
        rest = [p for p in photos if not p.favorite]
        return favs + rest
    with_people = [p for p in photos if p.person_count > 0]
    if with_people:
        ordered = sorted(with_people, key=lambda p: p.person_count, reverse=True)
        return ordered + [p for p in photos if p.person_count == 0]
    times = sorted(photos, key=lambda p: p.utc_instant)
    mid = times[len(times) // 2]
    return [mid] + [p for p in times if p is not mid]
