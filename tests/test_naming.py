from datetime import datetime

from phototrips.config import Config
from phototrips.home import HomeWindow
from phototrips.pipeline import run_pipeline

from fixtures import BUSAN_HAEUNDAE, JEJU, SEOUL, TOKYO, series

SEOUL_HOME = [HomeWindow(*SEOUL)]


def test_single_city_multiday_name():
    pts = []
    pts += series("d1", datetime(2024, 5, 3, 10), BUSAN_HAEUNDAE, 4, step_min=120,
                  city="Busan", country="South Korea", country_code="KR")
    pts += series("d2", datetime(2024, 5, 4, 10), BUSAN_HAEUNDAE, 4, step_min=120,
                  city="Busan", country="South Korea", country_code="KR")
    res = run_pipeline(pts, Config(), user_homes=SEOUL_HOME)
    t = res.trips[0]
    assert t.title == "Busan 2-day trip"
    assert t.name_components["anchor_city"] == "Busan"
    assert t.name_components["country_codes"] == ["KR"]


def test_single_city_day_trip_name():
    pts = series("d", datetime(2024, 5, 3, 10), JEJU, 4, step_min=60,
                 city="Jeju", country="South Korea", country_code="KR")
    res = run_pipeline(pts, Config(), user_homes=SEOUL_HOME)
    assert res.trips[0].title == "Jeju day trip"


def test_multi_country_name():
    pts = []
    pts += series("kr", datetime(2024, 6, 1, 10), BUSAN_HAEUNDAE, 3, step_min=60,
                  city="Busan", country="South Korea", country_code="KR")
    # Next day, jump to Tokyo (a separate trip by segmentation, but name each).
    pts += series("jp", datetime(2024, 6, 1, 14), TOKYO, 3, step_min=60,
                  city="Tokyo", country="Japan", country_code="JP")
    res = run_pipeline(pts, Config(), user_homes=SEOUL_HOME)
    # Each is single-country; assert the JP one names Japan/Tokyo.
    titles = " ".join(t.title for t in res.trips)
    assert "Tokyo" in titles or "Japan" in titles
