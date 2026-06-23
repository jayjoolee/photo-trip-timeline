from datetime import datetime

from phototrips.config import Config
from phototrips.home import HomeWindow
from phototrips.pipeline import run_pipeline

from fixtures import JEJU, SEOUL, pt, series

SEOUL_HOME = [HomeWindow(*SEOUL)]


def test_gps_less_photo_counted_into_matching_trip():
    pts = series("jeju", datetime(2024, 5, 3, 10), JEJU, 4, step_min=120)
    # A GPS-less photo taken during the trip window.
    pts.append(pt("nogps", datetime(2024, 5, 3, 16)))  # no latlon
    res = run_pipeline(pts, Config(), user_homes=SEOUL_HOME)
    assert len(res.trips) == 1
    trip = res.trips[0]
    assert trip.photo_count_gps == 4
    assert trip.photo_count_total == 5  # the GPS-less one was assigned


def test_orphan_gps_less_photo_excluded():
    pts = series("jeju", datetime(2024, 5, 3, 10), JEJU, 4, step_min=120)
    pts.append(pt("orphan", datetime(2024, 1, 1, 9)))  # well outside any trip
    res = run_pipeline(pts, Config(), user_homes=SEOUL_HOME)
    assert res.trips[0].photo_count_total == 4
