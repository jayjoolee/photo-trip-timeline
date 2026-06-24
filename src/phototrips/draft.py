"""Phase 2 — turn a trip from trips.json into a blog-draft *prompt pack*.

A prompt pack is a single Markdown file that bundles a trip's facts (dates,
day-by-day route, notable places, which photos to place) with a writing-style
guide, ready to paste into an LLM (Claude, ChatGPT, …) to get a blog-post draft.
This keeps the open-source tool free of any API key or model dependency.

Like timeline.md, a pack contains **place names only — never coordinates** (you
might paste it into a chat or share it), enforced by the same write-time guard.
"""

from __future__ import annotations

import re

from . import i18n

_COORD_RE = re.compile(r"-?\d{1,3}\.\d{3,}\s*,\s*-?\d{1,3}\.\d{3,}")


class CoordinateLeak(AssertionError):
    """Raised if a built pack contains a coordinate-shaped token."""


# Minimal label sets; the pack body is meant to be read by the trip's author.
_LABELS = {
    "ko": {
        "request": "블로그 글 작성 요청",
        "intro": ("아래 여행 정보를 바탕으로, 맨 끝의 「글쓰기 스타일」에 맞춰 "
                  "한국어 여행 블로그 글 초안을 써줘. 사진을 넣으면 좋은 자리에는 "
                  "`[사진: 설명]` 형태로 표시해줘."),
        "overview": "여행 개요", "period": "기간", "days": "일", "photos_label": "사진",
        "cities": "도시", "countries": "나라", "route": "날짜별 동선", "day": "일차",
        "top_places": "많이 담은 장소 (사진 수 순)", "rep_photos": "대표 사진 (이 자리에 넣으면 좋음)",
        "style": "글쓰기 스타일",
    },
    "en": {
        "request": "Blog draft request",
        "intro": ("Using the trip facts below, write a travel blog-post draft in the "
                  "voice described under \"Writing style\" at the end. Mark good spots "
                  "for a photo as `[photo: caption]`."),
        "overview": "Trip overview", "period": "Dates", "days": "days", "photos_label": "Photos",
        "cities": "Cities", "countries": "Countries", "route": "Day-by-day route", "day": "Day",
        "top_places": "Most-photographed places", "rep_photos": "Representative photos (good to place here)",
        "style": "Writing style",
    },
}


def build_prompt_pack(trip: dict, style_text: str, lang: str = "ko") -> str:
    """Build a paste-ready Markdown prompt pack for one trip (no coordinates)."""
    L = _LABELS.get(lang, _LABELS["ko"])
    nc = trip.get("name_components", {}) or {}
    lines: list[str] = []

    lines.append(f"# {L['request']}: {trip.get('title', '')}")
    lines.append("")
    lines.append(L["intro"])
    lines.append("")

    # Overview
    lines.append(f"## {L['overview']}")
    span = _span(trip.get("date_start", ""), trip.get("date_end", ""))
    lines.append(f"- {L['period']}: {span} ({trip.get('duration_days', '?')}{L['days']})")
    lines.append(f"- {L['photos_label']}: {i18n.photos(lang, trip.get('photo_count_total', 0))}")
    if nc.get("cities"):
        lines.append(f"- {L['cities']}: {', '.join(nc['cities'])}")
    if nc.get("countries"):
        lines.append(f"- {L['countries']}: {', '.join(nc['countries'])}")
    lines.append("")

    # Day-by-day (drop generic "city, region, country" fallback labels)
    lines.append(f"## {L['route']}")
    for d in trip.get("day_by_day", []):
        named = [p for p in d.get("places", []) if not _is_generic(p)]
        places = ", ".join(named) or "—"
        date = d.get("date", "")[5:].replace("-", ".")  # MM.DD
        lines.append(f"- {d.get('day')}{L['day']} ({date}): {places} — {i18n.photos(lang, d.get('photo_count', 0))}")
    lines.append("")

    # Notable places by photo count
    places = sorted(trip.get("place_sequence", []), key=lambda p: -p.get("photo_count", 0))
    notable = [p for p in places
               if p.get("photo_count", 0) >= 2 and not _is_generic(p.get("place_name", ""))][:10]
    if notable:
        lines.append(f"## {L['top_places']}")
        for i, p in enumerate(notable, 1):
            lines.append(f"{i}. {p.get('place_name', '?')} — {i18n.photos(lang, p.get('photo_count', 0))}")
        lines.append("")

    # Representative photos (place + time only; no uuid/coords needed for writing)
    reps = trip.get("representative_photos", [])
    if reps:
        lines.append(f"## {L['rep_photos']}")
        for p in reps:
            hint = p.get("caption_hint") or p.get("place_name") or ""
            when = (p.get("time", "") or "")[:16].replace("T", " ")
            lines.append(f"- {hint} ({when})")
        lines.append("")

    # Style guide
    lines.append("---")
    lines.append(f"## {L['style']}")
    lines.append(style_text.strip())
    lines.append("")

    text = "\n".join(lines) + "\n"
    _assert_no_coords(text)
    return text


def select_trips(doc: dict, trip_id: str | None, limit: int | None, all_: bool) -> list[dict]:
    """Pick trips from a trips.json doc: a specific id, 'auto', a limit, or all."""
    trips = doc.get("trips", [])
    if all_:
        return trips
    if trip_id and trip_id != "auto":
        match = [t for t in trips if t.get("trip_id") == trip_id]
        if not match:
            raise KeyError(f"trip_id {trip_id!r} not found")
        return match
    # auto / limit: most-photographed first
    ranked = sorted(trips, key=lambda t: -t.get("photo_count_total", 0))
    return ranked[: (limit or 1)]


DEFAULT_STYLE = (
    "Friendly, first-person travel writing. Keep it concrete: use the real place "
    "names, dates, and a few vivid details per day. No filler, no clichés, no emoji. "
    "A short hook to open, a natural day-by-day flow, and a brief reflective close."
)


def _is_generic(label: str) -> bool:
    """A 'city, region, country' fallback label (≥2 commas) rather than a real POI."""
    return label.count(",") >= 2


def _span(start: str, end: str) -> str:
    s, e = start[:10], end[:10]
    if not s:
        return ""
    if s == e:
        return s.replace("-", ".")
    return f"{s.replace('-', '.')}–{e[5:].replace('-', '.')}"


def _assert_no_coords(text: str) -> None:
    m = _COORD_RE.search(text)
    if m:
        raise CoordinateLeak(f"prompt pack would leak a coordinate: {m.group(0)!r}")
