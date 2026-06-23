# Contributing

Thanks for your interest! A few ground rules, mostly about privacy.

## Never commit personal data

This tool reads your photo library and produces files that contain your home
location and travel history. **None of that belongs in the repo.**

- `output/`, `trips.json`, `*.photoslibrary`, and `config.toml` are gitignored.
- A `.pre-commit` hook blocks committing those paths and any raw coordinate
  pair. Install it: `pip install pre-commit && pre-commit install`.
- **Never paste real `trips.json` or un-redacted output into an issue or PR.**
  Reproduce bugs with the synthetic fixtures in `tests/fixtures/` instead.

## Development

```bash
pip install -e ".[dev]"
pytest            # the whole algorithm core runs without a Mac/Photos library
```

`src/phototrips/extract.py` is the only module that touches `osxphotos`. Keep it
that way so the algorithm stays testable on synthetic data in CI.

## Tests first for risky areas

Home-location handling and trip segmentation are the highest-risk areas. New
behavior there should come with a fixture-backed test (see `tests/`).
