"""The only module that touches osxphotos / the Apple Photos library.

Isolating it here means the entire algorithm core (everything in pipeline.py and
below) imports and tests without a Mac or a Photos library. osxphotos is an
optional import; it is only required when you actually read real photos.
"""

from __future__ import annotations

from datetime import datetime

from .config import Config
from .model import PhotoPoint

# Apple Photos library schema versions this extraction has been validated
# against. osxphotos itself abstracts the schema and will raise on a version it
# cannot read, so this is informational only — used to print a heads-up, not to
# block. Extend it as new versions are confirmed working.
VALIDATED_PHOTOS_VERSIONS = {"5001"}


def load_points(cfg: Config, library_path: str | None = None) -> list[PhotoPoint]:
    """Read the Photos library and return normalized PhotoPoints.

    Includes GPS-less photos (the pipeline needs them for count assignment);
    screenshots, hidden, and trashed photos are excluded.
    """
    try:
        import osxphotos
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "osxphotos is required to read the Photos library: pip install osxphotos"
        ) from exc

    db = osxphotos.PhotosDB(dbfile=library_path) if library_path else osxphotos.PhotosDB()
    _warn_if_untested(db)

    photos = db.photos(images=True, movies=False, from_date=cfg.from_date, intrash=False)
    points: list[PhotoPoint] = []
    for p in photos:
        if getattr(p, "screenshot", False) or getattr(p, "hidden", False):
            continue
        points.append(_to_point(p))
    return points


def _to_point(p) -> PhotoPoint:
    loc = p.location or (None, None)
    place = p.place
    score = p.score
    persons = [n for n in (p.persons or []) if n and n != "_UNKNOWN_"]
    return PhotoPoint(
        uuid=p.uuid,
        dt=p.date,
        lat=loc[0],
        lon=loc[1],
        tzoffset=getattr(p, "tzoffset", 0) or 0,
        place_name=getattr(place, "name", None) if place else None,
        city=_first(place, "city"),
        state=_first(place, "state_province"),
        country=_first(place, "country"),
        country_code=getattr(getattr(place, "names", None), "country_code", None) if place else None,
        area_of_interest=_first(place, "area_of_interest"),
        ishome=bool(getattr(place, "ishome", False)) if place else False,
        score=getattr(score, "overall", None) if score else None,
        favorite=bool(getattr(p, "favorite", False)),
        person_count=len(persons),
        persons=persons,
        path=p.path,
    )


def _first(place, attr: str) -> str | None:
    """Read a names list field, guarding the always-a-list / maybe-empty shape."""
    if not place:
        return None
    names = getattr(place, "names", None)
    values = getattr(names, attr, None) if names else None
    if values:
        return values[0]
    return None


def _warn_if_untested(db) -> None:
    version = str(getattr(db, "db_version", "") or "")
    if version and version not in VALIDATED_PHOTOS_VERSIONS:
        import sys
        print(
            f"note: Photos library version {version} hasn't been explicitly "
            f"validated (known-good: {sorted(VALIDATED_PHOTOS_VERSIONS)}). "
            f"osxphotos reads it, but double-check the results look right.",
            file=sys.stderr,
        )
