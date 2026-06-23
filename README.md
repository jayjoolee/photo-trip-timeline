# photo-trip-timeline

Turn your geotagged photo library into an automatic **travel timeline**.

You travel, you take hundreds of photos — and then the "writing it up" never
happens because organizing it all is tedious. Your iPhone already stamps every
photo with **when** and **where**, and Apple Photos has already reverse-geocoded
those coordinates into **place names**. This tool reads that, figures out which
photos belong to which trip, and writes a clean timeline of *when you went
where* — the boring part, done for you.

```
# Photo Travel Timeline

## Busan 2-day trip — 2024.05.03–05.04 (2일, 142장)
Haeundae Beach → Gamcheon Culture Village → Jagalchi Market
- 1일차 (05.03): Haeundae Beach — 51장
- 2일차 (05.04): Gamcheon Culture Village, Jagalchi Market — 91장
```

It outputs two files:

- **`timeline.md`** — a shareable, human-readable timeline. **Contains place
  names only — never coordinates**, so it's safe to paste into a blog draft.
- **`trips.json`** — a structured record (kept private/gitignored) meant to feed
  a later blog-draft generator.

## Why not just use existing tools?

Plenty of projects extract GPS from photos or plot them on a map
([osxphotos](https://github.com/RhetTbull/osxphotos),
[mappics](https://github.com/antodippo/mappics), …). None of them answer the
question a travel blogger actually has: *"which photos are one trip, and where
did that trip go, day by day?"* That segmentation is what this tool does.

## How it works

1. **Extract** (`osxphotos`) — read each photo's time, GPS, and Apple's
   place-name hierarchy directly from the Photos library. No external geocoding,
   no network, fully on-device.
2. **Segment into trips** — the key step. Photos are sparse, so naive density
   clustering can't find trip boundaries. Instead we walk the timeline and cut a
   new trip on **home-aware** signals: returning near home, a long away-gap, a
   fast flight-sized jump, or a long overland move. A quiet rest day *inside* an
   overseas trip no longer splits it.
3. **Cluster places within each trip** (DBSCAN) — find the distinct spots you
   visited and order them into a route.
4. **Name & summarize** — derive a trip name from the places, pick a few
   representative photos (Apple's on-device aesthetic score), and render the
   timeline + JSON.

The whole algorithm core is pure Python and is exercised by the test suite on
synthetic data — **no Mac or Photos library needed to run the tests**. Only
`extract.py` touches `osxphotos`.

## Install

```bash
git clone https://github.com/joowonlee/photo-trip-timeline
cd photo-trip-timeline
pip install -e .
```

Requires macOS with the Apple Photos app, Python ≥ 3.10, and `osxphotos`
(installed automatically). Tested with osxphotos 0.76–0.79.

## Usage

```bash
# Simplest run — auto-detects your home, writes ./output/{timeline.md,trips.json}
phototrips

# If home can't be detected confidently, the tool refuses to guess. Either:
phototrips --home-lat 37.5665 --home-lon 126.9780   # tell it your home
phototrips --no-coords                              # or emit place names only

# Other options
phototrips --since 2022-07-01      # only photos on/after a date
phototrips --library /path/to/X.photoslibrary
phototrips --include-names         # include people's names in trips.json (off by default)
```

Multiple `--home-lat/--home-lon` pairs (with optional `--home-from/--home-until`)
handle a move during the covered period.

## Privacy

This tool reads your photos and knows where you live. It is built to keep that
private:

- **`timeline.md` never contains numeric coordinates** — only place names. A
  write-time assertion enforces this.
- **Home is fail-closed**: if it can't determine your home with high confidence,
  it stops and asks rather than guessing and leaking a near-home coordinate.
- **`trips.json`, the photo library, and `output/` are gitignored**, and a
  `pre-commit` hook blocks committing them or any coordinate-shaped token.
- **People's names are opt-in** (`--include-names`); by default only a count is
  recorded.

Install the guard: `pip install pre-commit && pre-commit install`.

## Roadmap

- **Phase 2 — blog drafts.** `trips.json` is designed as the contract for a
  follow-on step that turns each trip (plus its representative photos) into a
  blog-post draft in your own voice. Not built yet; the JSON already carries
  everything it will need (re-localizable place names, day-by-day structure,
  representative photo UUIDs, reliability signals).
- Optional map output (`folium`), and configurable thresholds via a config file.

## License

MIT
