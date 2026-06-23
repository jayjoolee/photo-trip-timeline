"""Regression tests for timezone-aware datetimes (what osxphotos returns).

The original fixtures used naive datetimes, which hid a crash comparing a
tz-aware photo time against the naive ``from_date`` cutoff, and a tzoffset
double-count in the ordering key. Real photos are always tz-aware.
"""

from datetime import datetime, timedelta, timezone

from phototrips.config import Config
from phototrips.home import HomeWindow
from phototrips.pipeline import run_pipeline

from fixtures import BUSAN_HAEUNDAE, SEOUL, TOKYO

KST = timezone(timedelta(hours=9))
JST = timezone(timedelta(hours=9))
SEOUL_HOME = [HomeWindow(*SEOUL)]


def _aware_series(prefix, start, latlon, n, step_min=60, tz=KST, **kw):
    from phototrips.model import PhotoPoint
    return [
        PhotoPoint(
            uuid=f"{prefix}-{i}",
            dt=(start + timedelta(minutes=step_min * i)).replace(tzinfo=tz),
            lat=latlon[0], lon=latlon[1],
            tzoffset=int(tz.utcoffset(None).total_seconds()),
            **kw,
        )
        for i in range(n)
    ]


def test_aware_datetimes_do_not_crash_and_filter_correctly():
    pts = _aware_series("bs", datetime(2024, 5, 3, 10), BUSAN_HAEUNDAE, 4,
                        city="Busan", country="South Korea", country_code="KR")
    # One photo before the since-cutoff must be excluded.
    pts += _aware_series("old", datetime(2020, 1, 1, 10), BUSAN_HAEUNDAE, 1)
    res = run_pipeline(pts, Config(), user_homes=SEOUL_HOME)
    assert len(res.trips) == 1
    assert res.trips[0].photo_count_gps == 4  # the 2020 photo filtered out


def test_cross_timezone_trip_orders_by_utc_instant():
    # A trip that crosses KST -> JST; events must stay correctly time-ordered.
    pts = _aware_series("seoul", datetime(2024, 6, 1, 8), SEOUL[0:2] if False else (37.46, 126.44), 2, tz=KST)
    pts += _aware_series("tokyo", datetime(2024, 6, 1, 13), TOKYO, 3, tz=JST,
                         city="Tokyo", country="Japan", country_code="JP")
    res = run_pipeline(pts, Config(), user_homes=SEOUL_HOME)
    # Should not crash; produces at least one trip with sane ordering.
    assert res.trips
    for t in res.trips:
        instants = [e.utc_instant for e in t.events]
        assert instants == sorted(instants)
