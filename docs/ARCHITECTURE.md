# Architecture

The system turns **7 heterogeneous monthly source files** — structured spreadsheets,
a digital PDF, a *scanned* image PDF, and phone screenshots — into one verified
workbook and one self-contained executive dashboard, with verification gates at every
step.

## Data flow

```mermaid
flowchart TD
    subgraph SRC["7 monthly source files"]
        A1["Weighted Average .xlsx"]
        A2["Retail Dept Summary .pdf<br/>(digital text)"]
        A3["Cost INIR Kitchen .pdf<br/>(SCANNED image)"]
        A4["Hourly Sales .xlsx"]
        A5["Price Override .xlsx"]
        A6["Customer Counts .jpg"]
        A7["Speed of Service .png"]
    end

    A1 & A4 & A5 -->|openpyxl| FILL["Fill the workbook<br/>(one row per month, per store)"]
    A2 -->|pdfplumber| FILL
    A3 & A6 & A7 -->|AI vision / OCR| FILL

    FILL --> WB[("Excel workbook<br/>source of record")]

    WB --> V1{{"verify_month.py<br/>consistency + MoM swings"}}
    V1 --> V2{{"flag_review.py<br/>3-month-average deviation"}}
    V2 --> BUILD["build_dashboard.py<br/>extract + inject into template"]
    BUILD --> DASH["Executive Dashboard .html<br/>(self-contained, offline)"]
    DASH --> V3{{"verify_sources.py<br/>dashboard ↔ workbook ↔ sources"}}
    V3 --> OUT["Deliverables:<br/>HTML + printable PDF + CSV"]

    style WB fill:#1f3864,color:#fff
    style DASH fill:#1baf7a,color:#fff
    style OUT fill:#269b8e,color:#fff
```

## Why an AI agent, not just a script

Four of the seven sources are structured (spreadsheets + one digital PDF) and are read
deterministically with `openpyxl` / `pdfplumber`. **Three are not machine-readable**: the
Cost INIR kitchen report is a *scanned image* PDF (no text layer), and the customer-count
and speed-of-service files are screenshots. Those require **AI vision** to read reliably.
This hybrid — vision for the unstructured inputs, deterministic Python for verification and
rendering — is the core design decision.

## Components

| Layer | File | Responsibility |
|---|---|---|
| **Fill** | (AI agent + human) | Read all 7 sources, write the month into the workbook |
| **Verify** | `src/verify_month.py` | Internal consistency (Total = C-Store + Kitchen) + MoM swings |
| **Flag** | `src/flag_review.py` | Flag values >1.5% off their trailing 3-month average |
| **Build** | `src/build_dashboard.py` | Extract verified figures, inject into `dashboard_template.html` |
| **Cross-check** | `src/verify_sources.py` | Re-confirm dashboard ↔ workbook ↔ original sources |
| **Template** | `src/dashboard_template.html` | The dashboard shell (4 placeholders, inline SVG + JS) |
| **Demo** | `sample/generate_sample.py` | Build a runnable dashboard from synthetic data (no workbook) |

## The template contract

`build_dashboard.py` (and the demo generator) inject four JSON payloads into the template:

| Placeholder | Contents |
|---|---|
| `__MONTHLY__` | `{ storeId: [ {month, sales, margin, kitchen mix, …} ] }` |
| `__EXTRA__` | `{ storeId: { inv: [...], override: [...] } }` |
| `__MONS__` | `["Jan", …, latest]` — auto-detected from the workbook |
| `__FLAGS__` | `{ storeId: { metric: note } }` — pending review flags |

Because the dashboard is **regenerated from the workbook**, it can never silently drift
from the numbers. Every build re-runs the integrity check and prints the group YTD total.

## Design constraints (learned in production)

- **Write the workbook with Excel COM, never `openpyxl`** — it contains charts, drawings,
  and embedded images that `openpyxl` would strip. `openpyxl` is read-only here.
- **The dashboard is one self-contained file** — inline SVG charts + vanilla JS, no CDN,
  so it works offline and prints cleanly. No build step, no framework.
- **Auto-detect the latest filled month** — next month "just works" with no code change.
