"""Synthetic, self-contained demo — no Photos library, no real location data.

Powers ``phototrips --demo`` and the README's demo GIF. It runs the exact
segmentation + render path the real CLI uses, but on a handful of hand-made
points for a fictional Busan trip with Seoul as a stand-in "home", so it can
never leak real photos or a real home coordinate.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .config import Config
from .home import HomeWindow
from .model import PhotoPoint
from .pipeline import run_pipeline
from .render_markdown import render_timeline

# Fictional coordinates: Seoul as a fake "home", a Busan trip away from it.
_SEOUL = (37.5665, 126.9780)
_HAEUNDAE = (35.1587, 129.1604)
_GAMCHEON = (35.0975, 129.0107)
_JAGALCHI = (35.0967, 129.0303)


def _series(prefix, start, latlon, n, *, step_min=8, **kw):
    return [
        PhotoPoint(uuid=f"{prefix}-{i}", dt=start + timedelta(minutes=step_min * i),
                   lat=latlon[0], lon=latlon[1], **kw)
        for i in range(n)
    ]


def demo_points() -> list[PhotoPoint]:
    common = dict(city="Busan", country="South Korea", country_code="KR")
    return (
        _series("d1", datetime(2024, 5, 3, 10), _HAEUNDAE, 51,
                place_name="Haeundae Beach", area_of_interest="Haeundae Beach", **common)
        + _series("d2a", datetime(2024, 5, 4, 11), _GAMCHEON, 60,
                  place_name="Gamcheon Culture Village", area_of_interest="Gamcheon Culture Village", **common)
        + _series("d2b", datetime(2024, 5, 4, 16), _JAGALCHI, 31,
                  place_name="Jagalchi Market", area_of_interest="Jagalchi Market", **common)
    )


def render_demo(lang: str = "en") -> str:
    result = run_pipeline(demo_points(), Config(), user_homes=[HomeWindow(*_SEOUL)])
    return render_timeline(result.trips, lang=lang)
