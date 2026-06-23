"""Render the shareable timeline.md — place names only, never coordinates.

timeline.md is the file a user might paste into a blog or an issue, so it must
not contain a home address or any raw lat/lon. We build it from labels only and
assert at write time that no coordinate-shaped token slipped through.
"""

from __future__ import annotations

import re

from .model import Trip
from .places import day_breakdown, simplify_sequence

# A lat/lon pair like "35.158, 129.160" or a lone signed decimal with >=3 dp.
_COORD_RE = re.compile(r"-?\d{1,3}\.\d{3,}\s*,\s*-?\d{1,3}\.\d{3,}")


class CoordinateLeak(AssertionError):
    """Raised if rendered markdown contains a coordinate-shaped token."""


def render_timeline(trips: list[Trip]) -> str:
    lines: list[str] = ["# Photo Travel Timeline", ""]
    if not trips:
        lines.append("_여행으로 묶인 사진이 없습니다._")
        return "\n".join(lines) + "\n"

    for t in trips:  # already reverse-chronological
        span = _span(t)
        header = (
            f"## {t.title} — {span} "
            f"({t.duration_days}일, {t.photo_count_total}장)"
        )
        lines.append(header)

        route = simplify_sequence(t.places)
        if route:
            lines.append(" → ".join(p.label for p in route))
        for day in day_breakdown(t):
            places = ", ".join(day["places"]) or "—"
            lines.append(
                f"- {day['day']}일차 ({day['date']:%m.%d}): {places} — {day['photo_count']}장"
            )
        lines.append("")

    text = "\n".join(lines) + "\n"
    _assert_no_coords(text)
    return text


def _span(t: Trip) -> str:
    s, e = t.date_start, t.date_end
    if s.date() == e.date():
        return f"{s:%Y.%m.%d}"
    return f"{s:%Y.%m.%d}–{e:%m.%d}"


def _assert_no_coords(text: str) -> None:
    m = _COORD_RE.search(text)
    if m:
        raise CoordinateLeak(
            f"timeline.md would leak a coordinate-shaped token: {m.group(0)!r}"
        )
