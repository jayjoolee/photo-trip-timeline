English | [简体中文](https://github.com/jayjoolee/photo-trip-timeline/blob/main/README.zh-CN.md) | [한국어](https://github.com/jayjoolee/photo-trip-timeline/blob/main/README.ko.md)

<h1 align="center">photo-trip-timeline</h1>

<p align="center">
Auto-detect trips from your Apple Photos and generate a shareable Markdown travel timeline —<br>
<b>place names only, your GPS coordinates never leave your Mac.</b>
</p>

<p align="center">
<a href="https://github.com/jayjoolee/photo-trip-timeline/actions/workflows/ci.yml"><img src="https://github.com/jayjoolee/photo-trip-timeline/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+"></a>
<a href="https://github.com/jayjoolee/photo-trip-timeline/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
<a href="https://github.com/jayjoolee/photo-trip-timeline/blob/main/CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs welcome"></a>
</p>

<p align="center">
<img src="https://raw.githubusercontent.com/jayjoolee/photo-trip-timeline/main/assets/demo.gif" alt="phototrips --demo" width="800">
</p>

You travel, you shoot hundreds of photos — and the write-up never happens because
organizing it is tedious. Your iPhone already stamps every photo with *when* and
*where*, and Apple Photos already turned those coordinates into *place names*.
`photo-trip-timeline` reads that on-device, figures out which photos belong to
which trip, and writes a clean day-by-day timeline of where you went — **without
ever putting a coordinate in the file you share.**

**[Install](#install) · [Quick start](#quick-start) · [Privacy](#privacy-by-design) · [How it works](#how-it-works)**

```markdown
# Photo Travel Timeline

## Busan 2-day trip — 2024.05.03–05.04 (2 days, 142 photos)
Haeundae Beach → Gamcheon Culture Village → Jagalchi Market
- Day 1 (05.03): Haeundae Beach — 51 photos
- Day 2 (05.04): Gamcheon Culture Village, Jagalchi Market — 91 photos
```

*(Try it yourself with `phototrips --demo` — no photo library needed.)*

## Features

- 🔒 **Coordinates never leave your Mac** — `timeline.md` is place-names-only,
  enforced by a write-time assertion that fails the run if a lat/lon-shaped token
  slips through.
- 🏠 **Fail-closed home detection** — if it can't identify your home with high
  confidence, it stops and asks instead of guessing and leaking a near-home spot.
- 🗺️ **Automatic trip segmentation** — home-aware boundaries (return-home,
  away-gap, flight-sized jump, overland move); a quiet rest day inside an overseas
  trip won't split it.
- 📍 **Day-by-day routes** — clusters the distinct spots in each trip and orders
  them into a readable route, with photo counts per day.
- 🌏 **Multi-language output** — `--lang en | ko | zh` for the timeline; this
  README ships in English, 简体中文, and 한국어.
- 🧪 **Trustworthy** — the algorithm core is `osxphotos`-free and covered by 31
  tests that run on synthetic data, no Mac required.

## Install

```bash
git clone https://github.com/jayjoolee/photo-trip-timeline
cd photo-trip-timeline
pip install -e .
```

Requires macOS with the Apple Photos app, Python ≥ 3.10, and `osxphotos`
(installed automatically). Validated against Apple Photos library version 5001;
`osxphotos` reads other versions too.

## Quick start

```bash
# Auto-detects your home, writes ./output/{timeline.md, trips.json}
phototrips

# See sample output immediately, without touching your library:
phototrips --demo
```

## Usage

```bash
phototrips --lang ko                 # timeline in Korean (en | ko | zh; default en)
phototrips --since 2022-07-01        # only photos on/after a date
phototrips --library /path/to/X.photoslibrary

# If home can't be detected confidently, the tool refuses to guess. Either:
phototrips --home-lat 37.5665 --home-lon 126.9780   # tell it your home
phototrips --no-coords                              # or emit place names only

phototrips --include-names           # include people's names in trips.json (off by default)
```

Multiple `--home-lat/--home-lon` pairs (with optional `--home-from/--home-until`)
handle a move during the covered period.

It writes two files:

- **`timeline.md`** — a shareable, human-readable timeline. **Place names only —
  never coordinates**, so it's safe to paste into a blog draft.
- **`trips.json`** — a structured record (gitignored) meant to feed a later
  blog-draft generator.

## Privacy by design

This tool reads your photos and knows where you live. It's built to keep that private:

- **`timeline.md` never contains numeric coordinates** — only place names, enforced
  by a write-time assertion.
- **Home is fail-closed** — low confidence means it stops and asks, rather than
  guessing and leaking a near-home coordinate.
- **`trips.json`, the photo library, and `output/` are gitignored**, and a
  `pre-commit` hook blocks committing them or any coordinate-shaped token.
- **People's names are opt-in** (`--include-names`); by default only a count is recorded.
- **No network** — reverse geocoding uses Apple's on-device place names; no external calls.

See [SECURITY.md](SECURITY.md). Install the commit guard: `pip install pre-commit && pre-commit install`.

## Why not just use existing tools?

Plenty of projects extract GPS from photos or plot them on a map
([osxphotos](https://github.com/RhetTbull/osxphotos),
[mappics](https://github.com/antodippo/mappics), …). None of them answer the
question a travel blogger actually has: *"which photos are one trip, and where did
that trip go, day by day?"* — and do it without putting your home on a map.

## How it works

1. **Extract** (`osxphotos`) — read each photo's time, GPS, and Apple's place-name
   hierarchy directly from the Photos library. No external geocoding, fully on-device.
2. **Segment into trips** — the key step. Photos are sparse, so naive density
   clustering can't find trip boundaries. Instead a trip is time spent *away from
   home*; near-home daily-life photos act as boundaries, not trips. Within an
   away-period it still splits on long gaps, flight-sized jumps, and overland moves.
3. **Cluster places within each trip** (DBSCAN) — find the distinct spots you
   visited and order them into a route.
4. **Name & summarize** — derive a trip name from the places, pick representative
   photos (Apple's on-device aesthetic score), and render the timeline + JSON.

Only `extract.py` touches `osxphotos`; everything downstream runs on plain data, so
the test suite exercises the whole algorithm without a Mac.

## Configuration

Thresholds (away distance, gap hours, jump/long-haul distances, place-cluster
radius, etc.) live in `config.py` as documented defaults and are overridable from
the CLI. Run `phototrips --help` for the full list.

## Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). `pytest` runs the full suite
without a Mac or Photos library. **Never paste real coordinates into issues or
PRs** — reproduce with `phototrips --demo` or the synthetic fixtures in `tests/`.

## Roadmap

- **Phase 2 — blog drafts.** `trips.json` is designed as the contract for a
  follow-on step that turns each trip (plus representative photos) into a
  blog-post draft in your own voice. The JSON already carries what it needs
  (re-localizable place names, day-by-day structure, photo UUIDs, reliability signals).
- Localized trip *titles* (currently English), optional map output (`folium`), PyPI release.

## License

MIT — see [LICENSE](LICENSE).
