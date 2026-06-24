# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `phototrips draft` (Phase 2): turn a trip in `trips.json` into a paste-ready
  blog-draft *prompt pack* — trip facts + a swappable writing-style guide for an
  LLM. Place names only, no coordinates. `--trip`, `--all`, `--style`, `--lang`.
- Localized `timeline.md` output (`--lang en|ko|zh`); English is the default.
- `phototrips --demo` prints a sample timeline from synthetic data (no Photos
  library needed) — also powers the README demo GIF.
- Multi-language READMEs (English, 简体中文, 한국어).
- GitHub Actions CI (Linux, Python 3.10–3.13) and an i18n drift-check workflow.

## [0.1.0] - 2026-06-23

### Added
- Initial MVP: read an Apple Photos library via `osxphotos`, detect trips from
  photo GPS + time, and render a Markdown travel timeline plus a private
  `trips.json`.
- Home-aware trip segmentation, within-trip place clustering (DBSCAN), trip
  naming, and representative-photo selection.
- Privacy by construction: coordinate-free `timeline.md`, fail-closed home
  detection, gitignore + pre-commit guards, opt-in person names.
