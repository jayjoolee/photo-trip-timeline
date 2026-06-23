"""Command-line entry point: photos -> trips -> timeline.md + trips.json."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .config import Config
from .extract import load_points
from .home import HomeWindow
from .pipeline import run_pipeline
from .render_json import build_json
from .render_markdown import render_timeline


def _parse_date(s: str) -> datetime:
    return datetime.fromisoformat(s)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="phototrips",
        description="Turn a geotagged Apple Photos library into a travel timeline.",
    )
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

    if args.demo:
        from .demo import render_demo
        print(render_demo(args.lang))
        return 0

    cfg = Config(no_coords=args.no_coords, include_names=args.include_names, lang=args.lang)
    if args.since:
        cfg.from_date = args.since

    user_homes = _user_homes(args)
    if len(args.home_lat) != len(args.home_lon):
        print("error: --home-lat and --home-lon must be given in matching pairs", file=sys.stderr)
        return 2

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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
