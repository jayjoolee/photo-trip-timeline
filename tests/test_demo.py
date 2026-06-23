"""Smoke test for the synthetic demo behind `phototrips --demo`.

Guards the README GIF: if the demo ever breaks, this fails in CI *before* anyone
records a broken timeline into the hero image.
"""

from phototrips.demo import render_demo


def test_demo_renders_expected_english_output():
    out = render_demo("en")
    assert "Busan 2-day trip" in out
    assert "Haeundae Beach" in out
    assert "Day 1" in out and "Day 2" in out
    assert "142 photos" in out  # 51 + 60 + 31
    # The demo must never contain a coordinate (render asserts this too).
    import re
    assert not re.search(r"-?\d{1,3}\.\d{3,}\s*,\s*-?\d{1,3}\.\d{3,}", out)


def test_demo_localized():
    assert "第1天" in render_demo("zh")
    assert "1일차" in render_demo("ko")
