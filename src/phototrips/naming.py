"""Trip naming from Apple's place hierarchy (free, offline, private).

Names are heuristics over the cities/regions/countries the trip touched. We also
stash raw ``name_components`` so the Phase-2 Korean LLM can re-localize instead
of being stuck with whatever locale string the device produced.
"""

from __future__ import annotations

from collections import Counter

from .config import Config
from .model import Trip

_MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def name_trip(trip: Trip, cfg: Config) -> tuple[str, dict]:
    photos = [m for e in trip.events for m in e.members]
    n = len(photos)

    cities = _ranked(p.city for p in photos)
    countries = _ranked(p.country for p in photos)
    country_codes = _ranked(p.country_code for p in photos)
    aois = Counter(p.area_of_interest for p in photos if p.area_of_interest)

    anchor_city = cities[0] if cities else None
    region = _modal(p.state for p in photos) or anchor_city

    month = f"{_MONTHS[trip.date_start.month]} {trip.date_start.year}"

    # Area-of-interest is only specific enough to headline if it dominates.
    aoi = None
    if aois:
        top_aoi, top_n = aois.most_common(1)[0]
        if top_n / n >= cfg.aoi_coverage_min:
            aoi = top_aoi

    if len(countries) >= 2:
        title = f"{countries[0]} & {countries[1]} {month}"
    elif len(cities) >= 2:
        title = f"{region} {month}"
    elif anchor_city:
        if trip.duration_days >= 2:
            title = f"{anchor_city} {trip.duration_days}-day trip"
        else:
            title = f"{anchor_city} day trip"
    else:
        title = f"Trip {month}"

    components = {
        "anchor_city": anchor_city,
        "cities": cities,
        "region": region,
        "countries": countries,
        "country_codes": country_codes,
        "area_of_interest": aoi,
        "month": month,
    }
    return title, components


def _ranked(values) -> list[str]:
    counts = Counter(v for v in values if v)
    return [v for v, _ in counts.most_common()]


def _modal(values) -> str | None:
    r = _ranked(values)
    return r[0] if r else None
