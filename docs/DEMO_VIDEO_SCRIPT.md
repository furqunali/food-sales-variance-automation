# Demo video — script & speech (≈3 minutes)

A short screen recording that walks through the monthly workflow and the dashboard.
Record your screen (Windows `Win+G`, OBS, or Loom) and read the voiceover. All figures
below use the **synthetic sample data** shipped in this repo.

> **[SCENE]** = what to show · *"speech"* = read aloud · `(action)` = what to click.

---

### 0 · Title (0:00–0:12)
**[SCENE]** The live demo dashboard, Overview tab.
*"This is a Food and Sales Budget Variance system for a four-store food-and-fuel operation.
I'll show how a two-hour monthly typing job became a one-command, self-verifying report."*

### 1 · The problem (0:12–0:40)
**[SCENE]** `docs/ARCHITECTURE.md` diagram (or the source list).
*"Every month there are seven source files — spreadsheets, a PDF, a scanned kitchen report,
and phone screenshots. Someone retyped all of it into one workbook, for four stores. Slow,
and easy to paste the wrong store or column."*

### 2 · Read the sources (0:40–1:10)
**[SCENE]** The seven source types.
*"Four are structured — read exactly by code. Three are images: a scanned PDF and two
screenshots. A plain script can't read those, so AI vision does — that's the key design
choice: vision only where it's needed, deterministic code everywhere else."*

### 3 · Verify + build (1:10–1:50)
**[SCENE]** A terminal running the pipeline.
*"One command does the work: it checks each store's total equals C-store plus kitchen, flags
any value that drifts more than one-and-a-half percent from its three-month trend, rebuilds
the dashboard, and cross-checks it back against the sources. If something's off, it names the
store, the metric, and the file to check."*

### 4 · Overview (1:50–2:20)
**[SCENE]** Overview tab.
*"This is what leadership sees. Year-to-date sales against budget, attainment per store, sales
composition, kitchen product mix. One store leads at over eighty percent; one lags near fifty
— flagged instantly."* `(let the donuts and store cards show)`

### 5 · Month selector + a store tab (2:20–2:50)
**[SCENE]** Change the month dropdown; open a store tab.
*"Pick any month and the whole view refocuses. Each store has the full picture — attainment
gauge, margin trend, cost buckets that erode margin, customer counts, ending inventory."*

### 6 · Share (2:50–3:05)
**[SCENE]** Print / CSV buttons; the Data tab.
*"It's one self-contained file — works offline, prints to a two-page summary, exports to CSV.
Drop the files, run one command, send. And next month is detected automatically."*

---

**Tips:** record at 1920×1080, browser zoom 100%, close notifications, speak slightly slower
than feels natural, and pause when you click.
