# Security & Privacy

This tool reads your photo library and knows where you live, so privacy *is* the
security model. The design goal: **your GPS coordinates and home location never
leave your Mac, and never land in a file you might share.**

## How privacy is enforced

- **`timeline.md` contains place names only — never coordinates.** A write-time
  assertion (`render_markdown.CoordinateLeak`) aborts the run if a lat/lon-shaped
  token would be written to the shareable file.
- **Home detection fails closed.** If the tool can't identify your home with high
  confidence, it stops and asks for `--home-lat/--home-lon` (or `--no-coords`)
  rather than guessing and leaking a near-home coordinate. See `home.py`.
- **`trips.json` (which does contain coordinates), the photo library, and
  `output/` are gitignored**, and a `pre-commit` hook blocks committing them or
  any coordinate-shaped token.
- **Person names are opt-in** (`--include-names`); by default only a count is stored.
- **No network.** Reverse geocoding uses Apple's on-device place names via
  `osxphotos`; the tool makes no external calls.

## Reporting a vulnerability

If you find a way the tool could leak a coordinate, home location, or other
personal data into shareable output, please report it privately via GitHub's
**Security → Report a vulnerability** (private advisory) rather than a public
issue. Include a reproduction using `phototrips --demo` or synthetic fixtures —
**never** real coordinates.
