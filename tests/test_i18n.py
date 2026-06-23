from datetime import datetime

from phototrips.config import Config
from phototrips.home import HomeWindow
from phototrips.pipeline import run_pipeline
from phototrips.render_markdown import render_timeline

from fixtures import BUSAN_HAEUNDAE, SEOUL, series

SEOUL_HOME = [HomeWindow(*SEOUL)]


def _trips():
    pts = series("d1", datetime(2024, 5, 3, 10), BUSAN_HAEUNDAE, 4, step_min=60,
                 area_of_interest="Haeundae Beach", city="Busan")
    return run_pipeline(pts, Config(), user_homes=SEOUL_HOME).trips


def test_english_is_default():
    out = render_timeline(_trips())
    assert "Photo Travel Timeline" in out
    assert "Day 1" in out
    assert "photos" in out
    assert "일차" not in out


def test_korean_structural_words():
    out = render_timeline(_trips(), lang="ko")
    assert "사진 여행 타임라인" in out
    assert "1일차" in out
    assert "장" in out


def test_chinese_structural_words():
    out = render_timeline(_trips(), lang="zh")
    assert "照片旅行时间线" in out
    assert "第1天" in out
    assert "张" in out


def test_unknown_lang_falls_back_to_english():
    out = render_timeline(_trips(), lang="fr")
    assert "Day 1" in out


def test_empty_localized():
    assert "No photos" in render_timeline([], lang="en")
    assert "없습니다" in render_timeline([], lang="ko")
    assert "暂无" in render_timeline([], lang="zh")
