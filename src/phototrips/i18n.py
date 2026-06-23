"""Localization for the rendered timeline.

Only the structural words of timeline.md are localized (title, "Day N", photo
counts, duration). Place names come from Apple's data and are left as-is. English
is the default so the tool reads naturally for a global audience; ``--lang ko``
or ``--lang zh`` switch the structural words.
"""

from __future__ import annotations

SUPPORTED = ("en", "ko", "zh")


def normalize_lang(lang: str | None) -> str:
    if not lang:
        return "en"
    code = lang.lower().replace("_", "-").split("-")[0]
    return code if code in SUPPORTED else "en"


def title(lang: str) -> str:
    return {
        "en": "Photo Travel Timeline",
        "ko": "사진 여행 타임라인",
        "zh": "照片旅行时间线",
    }[lang]


def empty(lang: str) -> str:
    return {
        "en": "_No photos were grouped into trips yet._",
        "ko": "_여행으로 묶인 사진이 없습니다._",
        "zh": "_暂无归入行程的照片。_",
    }[lang]


def duration(lang: str, days: int, photos: int) -> str:
    """The '(2 days, 142 photos)' parenthetical, per language."""
    return {
        "en": f"{days} {'day' if days == 1 else 'days'}, {photos} photos",
        "ko": f"{days}일, {photos}장",
        "zh": f"{days}天, {photos}张",
    }[lang]


def day_label(lang: str, n: int) -> str:
    """The 'Day 1' / '1일차' / '第1天' day marker."""
    return {
        "en": f"Day {n}",
        "ko": f"{n}일차",
        "zh": f"第{n}天",
    }[lang]


def photos(lang: str, n: int) -> str:
    """The per-day '51 photos' / '51장' / '51张' count."""
    return {
        "en": f"{n} photos",
        "ko": f"{n}장",
        "zh": f"{n}张",
    }[lang]
