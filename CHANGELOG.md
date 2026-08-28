# Changelog

All notable changes to this project. Newest first.

## [1.0.0] — 2026-08-28

First public release — a sanitized, self-contained showcase of the Food & Sales
Budget Variance automation.

### Added
- **Runnable demo** (`sample/generate_sample.py`) that builds the full executive
  dashboard from deterministic **synthetic** data — no workbook, no source files,
  no third-party dependencies.
- **Production tooling** (`src/`): `build_dashboard.py`, `verify_month.py`,
  `flag_review.py`, `verify_sources.py`, the dashboard template, and the field map.
- **Documentation** (`docs/`): architecture (with data-flow diagram), verification
  methodology, case study, and a demo-video script; screenshot gallery.
- **Live demo via GitHub Pages** — CI rebuilds the demo on every push and deploys it.
- **CI** that builds the demo and enforces the same integrity rules as the pipeline
  (Total = C-Store + Kitchen; kitchen mix sums to kitchen sales; no unsubstituted
  template placeholders).
- MIT license, `.gitignore` that blocks any real data from ever being committed.

### Notes
- All data in this repository is synthetic and for demonstration only. The real
  monthly workbook and source documents are confidential and are **not** included.
