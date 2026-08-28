# Case study — from two hours of typing to a verified one-click report

> All figures in the public repo use **synthetic sample data** for four fictional stores.
> The system was built for a real multi-store retail-fuel + kitchen operation; the numbers
> here are invented and resemble reality only in shape.

## The problem

A multi-store food & fuel operation produced a monthly **Food & Sales Budget Variance**
report by hand. Each cycle meant:

- opening **7 different source files** per month — spreadsheets, a digital PDF, a *scanned*
  kitchen report, and phone screenshots,
- retyping dozens of numbers into a single Excel workbook, **for four stores**,
- roughly **two hours** of manual entry and eyeballing,
- errors that were caught only by luck (a wrong store, a wrong column, a stale value),
- and no fast way for leadership to see *where margin was leaking* across stores.

## The solution

A hybrid pipeline: **AI vision** reads the three unstructured sources (scan + screenshots),
**deterministic Python** reads the four structured ones, verifies everything, and rebuilds a
self-contained executive dashboard from the workbook.

The monthly routine becomes:

1. Drop the 7 files in the inbox.
2. Fill the workbook (agent-assisted).
3. **One command** → verify → flag → build → cross-check.
4. Review flags, then hand over the dashboard.

## Before / after

| | Before (manual) | After (this system) |
|---|---|---|
| Monthly effort | ~2 hours typing + eyeballing | Drop files → one command → review |
| Error control | Caught only by luck | Three automatic gates before every send |
| Unstructured sources | Re-typed by hand | Read in place via AI vision |
| Output | A dense workbook | Workbook **+** interactive dashboard **+** printable PDF |
| Cross-store analysis | Manual | Month selector, per-store detail, full grid |
| Next month | Repeat everything | Latest month auto-detected — no code change |

## Impact

- **Time**: a multi-hour manual task becomes a few minutes of review.
- **Accuracy**: three independent verification gates catch the quiet errors manual entry
  misses — and the dashboard is regenerated from the workbook, so it can never drift.
- **Decision-making**: leadership gets an at-a-glance view — attainment per store, sales
  composition, kitchen product mix, margin erosion — with any month one click away.

## What this demonstrates (engineering)

- Multi-modal data ingestion (structured + digital PDF + **scanned image** + screenshots).
- Pragmatic use of **AI vision only where it's actually needed**, deterministic code elsewhere.
- Verification-first design: consistency, trend, and source-cross-check gates.
- A zero-dependency, offline, printable dashboard generated from a single template.
- An automation that scales to future months with no code changes.
