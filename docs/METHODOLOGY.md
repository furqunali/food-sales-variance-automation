# Verification methodology

The value of this system is not the dashboard — it's the **chain of trust** behind every
number. Three independent gates run every month; a figure has to survive all three.

## Gate 1 — Internal consistency (`verify_month.py`)

For the latest filled month, per store:

- **Total = C-Store + Kitchen** (to within a rounding dollar). A mismatch means a
  mis-typed or mis-pasted component.
- **Month-over-month swings**: store sales beyond ±15%, or any margin / GP% / shrink
  beyond ±5 percentage points, or override counts beyond ±50%, are flagged with the
  store, the metric, and the *source file to recheck*.

Output is a short "VERIFY THIS" list. Empty list → safe to proceed.

## Gate 2 — Trend deviation (`flag_review.py`)

Every tracked value is compared to the **average of the previous up-to-3 months**. Anything
more than **±1.5%** away is flagged for human recheck and shown on the dashboard as an
orange ⚑ banner and a per-row marker. Flags stay *pending* until explicitly approved:

```bash
python src/flag_review.py            # compute flags for the latest month
python src/flag_review.py --list     # review them
python src/flag_review.py --approve all
```

Approved flags disappear on the next build; next month re-flags fresh. This catches the
quiet errors that don't break internal consistency — a stale value, a transposed digit.

## Gate 3 — Source cross-check (`verify_sources.py`)

The strongest gate: it re-derives the numbers straight from the original documents and
compares them to what the dashboard shows.

| Check | Dashboard value | Compared against |
|---|---|---|
| A | dashboard HTML | the workbook (faithful reflection) |
| B | GP% before/after, discount, kitchen $, INIR | Weighted Average source |
| C | C-store retail actual | Retail Dept Summary PDF (parsed) |
| D | price-override counts | DR Price Override source |
| E | kitchen product-mix sum | kitchen sales (internal) |

Image / scanned sources (Cost INIR kitchen, customer counts, speed-of-service) are read
by AI vision at fill time and listed for manual sign-off — they can't be re-parsed
deterministically, so they're called out explicitly rather than silently trusted.

## What this catches in practice

The consistency and trend rules have, in real monthly cycles, surfaced concrete errors of
exactly the kind that used to slip through manual entry:

- a wrong **store's** column pasted into the ending-inventory block,
- the right store but the **wrong column** (sales pasted where cost belonged),
- a **stale** kitchen-shrink value that no longer matched its source.

None of these break a formula — they just quietly make the report wrong. The gates make
them loud.

## The field map

Every field's exact source and destination cell is documented in
[`../src/FIELD_SOURCE_CELL_MAP.md`](../src/FIELD_SOURCE_CELL_MAP.md) — the recipe that
makes the monthly fill reproducible and auditable.
