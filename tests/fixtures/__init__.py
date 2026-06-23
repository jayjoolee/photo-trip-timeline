"""Synthetic geo-temporal fixtures. No real photos, ever.

Coordinates are real-world city points only so distances are realistic; none of
them is anyone's home.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from phototrips.model import PhotoPoint

# Reference points (lat, lon)
SEOUL = (37.5665, 126.9780)
JEJU = (33.4996, 126.5312)
BUSAN_HAEUNDAE = (35.1587, 129.1604)
BUSAN_GAMCHEON = (35.0975, 129.0107)
GANGNEUNG = (37.7519, 128.8761)
TOKYO = (35.6809, 139.7670)
OSAKA = (34.6937, 135.5023)
DAEJEON = (36.3504, 127.3845)


def pt(uuid: str, dt: datetime, latlon=None, **kw) -> PhotoPoint:
    lat, lon = (latlon if latlon else (None, None))
    return PhotoPoint(uuid=uuid, dt=dt, lat=lat, lon=lon, **kw)


def series(prefix: str, start: datetime, latlon, n: int, step_min: int = 60, **kw):
    """n photos at one location, step_min minutes apart, starting at ``start``."""
    return [
        pt(f"{prefix}-{i}", start + timedelta(minutes=step_min * i), latlon, **kw)
        for i in range(n)
    ]
