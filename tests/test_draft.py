"""Tests for the Phase 2 prompt-pack builder (osxphotos-free, synthetic data)."""

import pytest

from phototrips.draft import (
    DEFAULT_STYLE,
    CoordinateLeak,
    build_prompt_pack,
    select_trips,
)

TRIP = {
    "trip_id": "2024-05-03-busan",
    "title": "Busan 2-day trip",
    "name_components": {"cities": ["Busan"], "countries": ["South Korea"]},
    "date_start": "2024-05-03T10:00:00+09:00",
    "date_end": "2024-05-04T18:00:00+09:00",
    "duration_days": 2,
    "photo_count_total": 142,
    "place_sequence": [
        {"place_name": "Haeundae Beach", "photo_count": 51, "lat": 35.158, "lon": 129.160},
        {"place_name": "Gamcheon Culture Village", "photo_count": 60, "lat": 35.0975, "lon": 129.0107},
    ],
    "day_by_day": [
        {"day": 1, "date": "2024-05-03", "places": ["Haeundae Beach"], "photo_count": 51},
        {"day": 2, "date": "2024-05-04", "places": ["Gamcheon Culture Village"], "photo_count": 91},
    ],
    "representative_photos": [
        {"caption_hint": "Haeundae Beach, Busan", "time": "2024-05-03T11:00:00+09:00",
         "place_name": "Haeundae Beach", "lat": 35.158, "lon": 129.16},
    ],
}


def test_pack_has_sections_and_style():
    pack = build_prompt_pack(TRIP, "내 글쓰기 스타일: 평어체.", lang="ko")
    assert "Busan 2-day trip" in pack
    assert "여행 개요" in pack
    assert "날짜별 동선" in pack
    assert "1일차" in pack and "2일차" in pack
    assert "Haeundae Beach" in pack
    assert "내 글쓰기 스타일: 평어체." in pack  # style text embedded


def test_pack_never_contains_coordinates():
    # The trip dict carries lat/lon, but the pack must not leak them.
    pack = build_prompt_pack(TRIP, DEFAULT_STYLE, lang="ko")
    import re
    assert not re.search(r"-?\d{1,3}\.\d{3,}\s*,\s*-?\d{1,3}\.\d{3,}", pack)
    assert "129.16" not in pack


def test_pack_english():
    pack = build_prompt_pack(TRIP, DEFAULT_STYLE, lang="en")
    assert "Trip overview" in pack
    assert "Day-by-day route" in pack


def test_coordinate_leak_guard_fires():
    bad_style = "Reference point 35.1234, 129.5678 please."
    with pytest.raises(CoordinateLeak):
        build_prompt_pack(TRIP, bad_style, lang="ko")


def test_select_trips_auto_picks_most_photographed():
    doc = {"trips": [
        {"trip_id": "a", "photo_count_total": 10},
        {"trip_id": "b", "photo_count_total": 99},
    ]}
    assert select_trips(doc, "auto", None, False)[0]["trip_id"] == "b"


def test_select_trips_by_id_and_missing():
    doc = {"trips": [{"trip_id": "a", "photo_count_total": 10}]}
    assert select_trips(doc, "a", None, False)[0]["trip_id"] == "a"
    with pytest.raises(KeyError):
        select_trips(doc, "nope", None, False)
