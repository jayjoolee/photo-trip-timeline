from datetime import datetime

from phototrips.config import Config
from phototrips.home import HomeWindow, detect_home
from phototrips.pipeline import run_pipeline
from phototrips.render_markdown import CoordinateLeak, render_timeline

from fixtures import JEJU, SEOUL, pt, series


def test_user_supplied_home_overrides_inference():
    pts = series("x", datetime(2024, 5, 1, 23), SEOUL, 10, step_min=10)
    res = detect_home(pts, Config(), user_homes=[HomeWindow(*JEJU)])
    assert res.confidence == "user_supplied"
    assert res.for_date(datetime(2024, 5, 1)) == JEJU


def test_apple_ishome_flag_detected_high():
    pts = series("home", datetime(2024, 5, 1, 23), SEOUL, 5, step_min=30, ishome=True)
    res = detect_home(pts, Config())
    assert res.confidence == "high"
    assert abs(res.windows[0].lat - SEOUL[0]) < 0.01


def test_night_cluster_detected_high():
    # Many night photos clustered at home, a few daytime elsewhere.
    pts = []
    pts += [pt(f"n{i}", datetime(2024, 5, i + 1, 23), SEOUL) for i in range(6)]
    pts += series("day", datetime(2024, 5, 2, 13), JEJU, 3, step_min=60)
    res = detect_home(pts, Config())
    assert res.confidence == "high"
    assert abs(res.windows[0].lat - SEOUL[0]) < 0.05


def test_no_signal_is_low_confidence():
    # Scattered daytime photos, no night cluster, no ishome.
    pts = series("day", datetime(2024, 5, 1, 13), JEJU, 2, step_min=60)
    res = detect_home(pts, Config())
    assert res.confidence == "low"
    assert res.windows == []


def test_low_confidence_pipeline_then_fail_closed_contract():
    # Pipeline still runs; the CLI is what fails closed. Confirm confidence.
    pts = series("day", datetime(2024, 5, 1, 13), JEJU, 2, step_min=60)
    res = run_pipeline(pts, Config())
    assert res.home.confidence == "low"


def test_timeline_never_contains_coordinates():
    # Even a malicious place label must be caught by the write-time assertion.
    from phototrips.model import Place, Trip, Event

    leak_place = Place(
        label="35.158, 129.160",  # a coordinate disguised as a name
        city="Busan", lat=35.158, lon=129.16, photo_count=3,
        time_start=datetime(2024, 5, 3, 10), time_end=datetime(2024, 5, 3, 12),
        member_uuids=["a"],
    )
    trip = Trip(events=[Event(members=[pt("a", datetime(2024, 5, 3, 10), (35.158, 129.16))])])
    trip.title = "Busan day trip"
    trip.places = [leak_place]
    try:
        render_timeline([trip])
        assert False, "expected CoordinateLeak"
    except CoordinateLeak:
        pass
