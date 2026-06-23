from datetime import datetime

from phototrips.config import Config
from phototrips.home import HomeWindow
from phototrips.pipeline import run_pipeline
from phototrips.places import simplify_sequence

from fixtures import BUSAN_GAMCHEON, BUSAN_HAEUNDAE, SEOUL, series

SEOUL_HOME = [HomeWindow(*SEOUL)]


def test_distinct_places_clustered_and_ordered():
    pts = []
    pts += series("hd", datetime(2024, 5, 3, 10), BUSAN_HAEUNDAE, 4, step_min=30,
                  area_of_interest="Haeundae Beach", city="Busan")
    pts += series("gc", datetime(2024, 5, 3, 15), BUSAN_GAMCHEON, 4, step_min=30,
                  area_of_interest="Gamcheon Culture Village", city="Busan")
    res = run_pipeline(pts, Config(), user_homes=SEOUL_HOME)
    trip = res.trips[0]
    labels = [p.label for p in trip.places]
    assert "Haeundae Beach" in labels
    assert "Gamcheon Culture Village" in labels
    # Ordered by first-photo time: Haeundae before Gamcheon.
    assert labels.index("Haeundae Beach") < labels.index("Gamcheon Culture Village")


def test_day_breakdown_counts_revisited_place_on_each_day():
    # Haeundae on day 1 AND day 2 -> both days must appear with correct counts,
    # even though the place cluster spans both days.
    from phototrips.places import day_breakdown
    pts = []
    pts += series("d1", datetime(2024, 5, 3, 10), BUSAN_HAEUNDAE, 5, step_min=30,
                  area_of_interest="Haeundae Beach", city="Busan")
    pts += series("d2", datetime(2024, 5, 4, 10), BUSAN_HAEUNDAE, 3, step_min=30,
                  area_of_interest="Haeundae Beach", city="Busan")
    res = run_pipeline(pts, Config(), user_homes=SEOUL_HOME)
    days = day_breakdown(res.trips[0])
    assert [d["day"] for d in days] == [1, 2]
    assert days[0]["photo_count"] == 5
    assert days[1]["photo_count"] == 3
    assert days[1]["places"] == ["Haeundae Beach"]


def test_simplify_collapses_same_label_run():
    pts = []
    pts += series("a", datetime(2024, 5, 3, 10), BUSAN_GAMCHEON, 3, step_min=10,
                  area_of_interest="Gamcheon Culture Village", city="Busan")
    pts += series("b", datetime(2024, 5, 3, 11), (35.0980, 129.0112), 3, step_min=10,
                  area_of_interest="Gamcheon Culture Village", city="Busan")
    res = run_pipeline(pts, Config(), user_homes=SEOUL_HOME)
    trip = res.trips[0]
    simplified = simplify_sequence(trip.places)
    assert len(simplified) == 1
    assert simplified[0].label == "Gamcheon Culture Village"
