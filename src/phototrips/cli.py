"""Command-line entry point.

Default (no subcommand): photos -> trips -> timeline.md + trips.json.
`phototrips draft`: trips.json -> per-trip blog-draft prompt packs (Phase 2).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .config import Config
from .home import HomeWindow


def _parse_date(s: str) -> datetime:
    return datetime.fromisoformat(s)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="phototrips",
        description="Turn a geotagged Apple Photos library into a travel timeline.",
    )
    # Timeline args live on the main parser so `phototrips [opts]` works with no
    # subcommand (the default behavior).
    p.add_argument("--library", help="Path to a .photoslibrary (default: system library)")
    p.add_argument("--output", default="output", help="Output directory (default: ./output)")
    p.add_argument("--since", type=_parse_date, help="Only photos on/after this date (YYYY-MM-DD)")
    p.add_argument("--home-lat", type=float, action="append", default=[],
                   help="Home latitude (repeatable, pairs with --home-lon)")
    p.add_argument("--home-lon", type=float, action="append", default=[],
                   help="Home longitude (repeatable, pairs with --home-lat)")
    p.add_argument("--home-from", type=_parse_date, action="append", default=[],
                   help="Start date a home becomes effective (handles relocation)")
    p.add_argument("--home-until", type=_parse_date, action="append", default=[],
                   help="End date a home stops being effective")
    p.add_argument("--demo", action="store_true",
                   help="Print a sample timeline from synthetic data (no Photos library needed)")
    p.add_argument("--lang", choices=["en", "ko", "zh"], default="en",
                   help="Language for timeline.md structural words (default: en)")
    p.add_argument("--no-coords", action="store_true",
                   help="Emit zero numeric coordinates anywhere (place names only)")
    p.add_argument("--include-names", action="store_true",
                   help="Opt person names into trips.json (default: counts only)")

    sub = p.add_subparsers(dest="command")
    d = sub.add_parser("draft", help="Generate blog-draft prompt packs from trips.json")
    d.add_argument("--input", default="output/trips.json", help="Path to trips.json")
    d.add_argument("--output", default="output/drafts", help="Where to write packs")
    d.add_argument("--trip", help="trip_id to draft, or 'auto' for the most-photographed")
    d.add_argument("--limit", type=int, help="With auto-select, draft the top N trips")
    d.add_argument("--all", action="store_true", help="Draft every trip")
    d.add_argument("--style", help="Path to a writing-style markdown file (default: built-in)")
    d.add_argument("--lang", dest="draft_lang", choices=["ko", "en"], default="ko",
                   help="Language of the prompt pack (default: ko)")
    return p


def _user_homes(args) -> list[HomeWindow]:
    homes: list[HomeWindow] = []
    for i, (lat, lon) in enumerate(zip(args.home_lat, args.home_lon)):
        start = args.home_from[i] if i < len(args.home_from) else None
        until = args.home_until[i] if i < len(args.home_until) else None
        homes.append(HomeWindow(lat=lat, lon=lon, start=start, until=until))
    return homes


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "draft":
        return run_draft(args)

    if args.demo:
        from .demo import render_demo
        print(render_demo(args.lang))
        return 0

    return run_timeline(args)


def run_timeline(args) -> int:
    from .extract import load_points
    from .pipeline import run_pipeline
    from .render_json import build_json
    from .render_markdown import render_timeline

    cfg = Config(no_coords=args.no_coords, include_names=args.include_names, lang=args.lang)
    if args.since:
        cfg.from_date = args.since

    if len(args.home_lat) != len(args.home_lon):
        print("error: --home-lat and --home-lon must be given in matching pairs", file=sys.stderr)
        return 2
    user_homes = _user_homes(args)

    points = load_points(cfg, library_path=args.library)
    result = run_pipeline(points, cfg, user_homes=user_homes or None)

    # Fail closed: never guess a home and write coordinates near it.
    if result.home.confidence == "low" and not cfg.no_coords:
        print(
            "error: could not confidently determine your home location.\n"
            "  Re-run with --home-lat <lat> --home-lon <lon>, or use --no-coords\n"
            "  to emit place names only (no coordinates anywhere).",
            file=sys.stderr,
        )
        return 1

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    timeline = render_timeline(result.trips, lang=cfg.lang)
    (out / "timeline.md").write_text(timeline, encoding="utf-8")

    photos_by_uuid = {p.uuid: p for p in points if p.has_gps}
    doc = build_json(result, cfg, photos_by_uuid, generated_at=datetime.now())
    (out / "trips.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"Wrote {len(result.trips)} trips "
        f"({len(result.minor_trips)} minor) to {out}/timeline.md and {out}/trips.json "
        f"[home confidence: {result.home.confidence}]"
    )
    return 0


def run_draft(args) -> int:
    from .draft import DEFAULT_STYLE, build_prompt_pack, select_trips

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"error: {in_path} not found. Run `phototrips` first to create it.", file=sys.stderr)
        return 1
    doc = json.loads(in_path.read_text(encoding="utf-8"))

    style_text = Path(args.style).read_text(encoding="utf-8") if args.style else DEFAULT_STYLE

    try:
        trips = select_trips(doc, args.trip, args.limit, args.all)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not trips:
        print("error: no trips found in trips.json", file=sys.stderr)
        return 1

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    for trip in trips:
        pack = build_prompt_pack(trip, style_text, lang=args.draft_lang)
        path = out / f"{trip['trip_id']}.md"
        path.write_text(pack, encoding="utf-8")
        print(f"Wrote {path}  ({trip.get('title', '')}, {trip.get('photo_count_total', 0)} photos)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
