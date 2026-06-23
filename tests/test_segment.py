from datetime import datetime, timedelta

from phototrips.config import Config
from phototrips.home import HomeWindow
from phototrips.pipeline import run_pipeline

from fixtures import (
    BUSAN_HAEUNDAE, DAEJEON, GANGNEUNG, JEJU, OSAKA, SEOUL, TOKYO, pt, series,
)

SEOUL_HOME = [HomeWindow(*SEOUL)]


def _run(points):
    return run_pipeline(points, Config(), user_homes=SEOUL_HOME)


def test_overseas_quiet_day_stays_one_trip():
    # A 3-day Jeju trip with a 30h photo-quiet gap in the middle.
    pts = []
    pts += series("d1", datetime(2024, 5, 3, 10), JEJU, 3, step_min=120)
    # 30h gap (< 48h away threshold) -> must NOT split.
    pts += series("d3", datetime(2024, 5, 4, 20), JEJU, 3, step_min=120)
    res = _run(pts)
    # The 30h quiet gap (< 48h away threshold) must keep this as ONE trip.
    assert len(res.trips) == 1
    # Last photo (20:00 + 2x120min) crosses midnight into the 3rd calendar day.
    assert res.trips[0].duration_days == 3


def test_return_home_splits_two_trips():
    pts = []
    pts += series("jeju", datetime(2024, 5, 3, 10), JEJU, 4, step_min=120)
    pts += [pt("home", datetime(2024, 5, 6, 22), SEOUL)]  # back home
    pts += series("busan", datetime(2024, 5, 10, 10), BUSAN_HAEUNDAE, 4, step_min=120)
    res = _run(pts)
    assert len(res.trips) == 2


def test_flight_jump_splits_destinations():
    # Tokyo then Osaka 3h later: >100km within 12h -> two trips.
    pts = []
    pts += series("tok", datetime(2024, 6, 1, 9), TOKYO, 3, step_min=60)
    pts += series("osa", datetime(2024, 6, 1, 15), OSAKA, 3, step_min=60)
    res = _run(pts)
    assert len(res.trips) == 2


def test_longhaul_overland_splits():
    # Daejeon -> Busan (~190-200km) in 10h, both away from Seoul.
    pts = []
    pts += series("dj", datetime(2024, 7, 1, 9), DAEJEON, 3, step_min=60)
    pts += series("bs", datetime(2024, 7, 1, 19), BUSAN_HAEUNDAE, 3, step_min=60)
    res = _run(pts)
    assert len(res.trips) == 2


def test_far_day_trip_is_rescued_not_deleted():
    # Two photos, <2h, far from home (>100km) -> rescued, stays significant.
    pts = series("gn", datetime(2024, 8, 1, 11), GANGNEUNG, 2, step_min=30)
    res = _run(pts)
    assert len(res.trips) == 1
    assert res.trips[0].rescued is True
    assert res.minor_trips == []


def test_near_home_daily_life_is_not_a_trip():
    # Photos ~10km from home (everyday life in the home city) must NOT become a
    # trip at all — this is the bug that produced hundreds of "서울 2-day trip".
    near = (37.65, 127.05)  # ~10km from Seoul -> within away_km, daily life
    pts = series("life", datetime(2024, 9, 1, 13), near, 8, step_min=30)
    res = _run(pts)
    assert res.trips == []
    assert res.minor_trips == []


def test_single_far_photo_is_not_a_trip():
    # One stray geotagged photo far away (a flight-path / layover snap) must not
    # become a trip even though it's far from home — it goes to minor.
    pts = series("stray", datetime(2024, 8, 1, 11), GANGNEUNG, 1)
    res = _run(pts)
    assert res.trips == []
    assert len(res.minor_trips) == 1


def test_mid_distance_weak_trip_is_demoted_to_minor():
    # ~70km away (a trip by distance) but only 2 photos / short span, and under
    # the 100km rescue distance -> demoted to minor, not a headline trip.
    mid = (38.15, 127.4)  # ~70km from Seoul: away but not far enough to rescue
    pts = series("blip", datetime(2024, 9, 1, 13), mid, 2, step_min=20)
    res = _run(pts)
    assert res.trips == []
    assert len(res.minor_trips) == 1
    assert res.minor_trips[0].minor is True
