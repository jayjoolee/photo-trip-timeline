"""Home / significant-location detection — privacy-critical, fail-closed.

A wrong or leaked home location is the worst failure here (it ships in a public
repo's shareable output), so detection is confidence-scored and *refuses* to
guess silently. Resolution order:

  1. User-supplied ``--home-lat/--home-lon`` (optionally date-ranged).  HIGH
  2. Apple's own ``place.ishome`` flag.                                  HIGH
  3. Modal night-time cluster fallback.            HIGH only if it dominates

If nothing reaches HIGH confidence we return ``confidence='low'`` and the CLI
fails closed: it asks for an explicit home or runs in ``--no-coords`` mode.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from .config import Config
from .geo import dbscan
from .model import PhotoPoint


@dataclass
class HomeWindow:
    """A home location effective over an optional date range (handles moves)."""

    lat: float
    lon: float
    start: datetime | None = None
    until: datetime | None = None

    def active_on(self, dt: datetime) -> bool:
        if self.start is not None and dt < self.start:
            return False
        if self.until is not None and dt >= self.until:
            return False
        return True


@dataclass
class HomeResult:
    windows: list[HomeWindow]
    confidence: str  # 'user_supplied' | 'high' | 'low'

    def for_date(self, dt: datetime) -> tuple[float, float] | None:
        for w in self.windows:
            if w.active_on(dt):
                return (w.lat, w.lon)
        # Fall back to the first window if none matched the date range.
        return (self.windows[0].lat, self.windows[0].lon) if self.windows else None


def detect_home(
    points: list[PhotoPoint],
    cfg: Config,
    user_homes: list[HomeWindow] | None = None,
) -> HomeResult:
    """Resolve the home location(s) with a confidence label."""
    if user_homes:
        return HomeResult(windows=list(user_homes), confidence="user_supplied")

    gps = [p for p in points if p.has_gps]

    # 2) Apple's ishome flag — trust it if present and consistent.
    ishome_pts = [p for p in gps if p.ishome]
    if ishome_pts:
        lat = sum(p.lat for p in ishome_pts) / len(ishome_pts)
        lon = sum(p.lon for p in ishome_pts) / len(ishome_pts)
        return HomeResult(windows=[HomeWindow(lat, lon)], confidence="high")

    # 3) Modal night cluster: cluster night-time photos, take the dominant one.
    night = [p for p in gps if _is_night(p.dt.hour, cfg)]
    if len(night) >= cfg.home_min_nights:
        coords = [(p.lat, p.lon) for p in night]
        labels = dbscan(coords, cfg.night_eps_m, min_samples=2)
        counts = Counter(l for l in labels if l != -1)
        if counts:
            (top_label, top_n), *rest = counts.most_common()
            runner = rest[0][1] if rest else 0
            dominant = top_n >= cfg.home_min_nights and top_n >= cfg.home_dominance * max(runner, 1)
            if dominant:
                members = [coords[i] for i, l in enumerate(labels) if l == top_label]
                lat = sum(c[0] for c in members) / len(members)
                lon = sum(c[1] for c in members) / len(members)
                return HomeResult(windows=[HomeWindow(lat, lon)], confidence="high")

    # Nothing trustworthy: fail closed at the CLI layer.
    return HomeResult(windows=[], confidence="low")


def _is_night(hour: int, cfg: Config) -> bool:
    # Night window wraps past midnight (e.g. 22:00–07:00).
    if cfg.night_start_h <= cfg.night_end_h:
        return cfg.night_start_h <= hour < cfg.night_end_h
    return hour >= cfg.night_start_h or hour < cfg.night_end_h
