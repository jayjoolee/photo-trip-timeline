# Contributing

Thanks for your interest! A few ground rules, mostly about privacy.

## Never commit personal data

This tool reads your photo library and produces files that contain your home
location and travel history. **None of that belongs in the repo.**

- `output/`, `trips.json`, `*.photoslibrary`, and `config.toml` are gitignored.
- A `.pre-commit` hook blocks committing those paths and any raw coordinate
  pair. Install it: `pip install pre-commit && pre-commit install`.
- **Never paste real `trips.json` or un-redacted output into an issue or PR.**
  Reproduce bugs with `phototrips --demo` or the synthetic fixtures in
  `tests/fixtures/` instead.

## Development

```bash
pip install -e ".[dev]"
pytest               # the whole algorithm core runs without a Mac/Photos library
phototrips --demo    # sample output from synthetic data (no library needed)
```

`src/phototrips/extract.py` is the only module that touches `osxphotos`. Keep it
that way so the algorithm stays testable on synthetic data in CI.

## Translations

`README.md` (English) is canonical; `README.zh-CN.md` and `README.ko.md` are
translations. If you change `README.md`, update the translations too (a CI check
warns when they drift). Keep badges, code blocks, and the demo image identical
across all three — translate prose only.

## Regenerating the demo GIF

`assets/demo.gif` is built from `assets/demo.tape` with
[VHS](https://github.com/charmbracelet/vhs): `brew install vhs && vhs assets/demo.tape`.
It records `phototrips --demo` (synthetic data only), so it never leaks real data.

## Tests first for risky areas

Home-location handling and trip segmentation are the highest-risk areas. New
behavior there should come with a fixture-backed test (see `tests/`).
