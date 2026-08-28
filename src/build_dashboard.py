#!/usr/bin/env python3
"""
build_dashboard.py  —  Regenerate the HTML Executive Dashboard from the Excel report.

WHAT IT DOES
  1. Reads the corrected Excel workbook (data_only) — the 4 store tabs.
  2. Extracts the verified monthly figures (Jan..current month) for every store,
     PLUS the full per-store detail that the Excel carries:
       - food-margin breakdown (discount, wastage, sampling, spoilage, logo cups, shrink $)
       - customer counts (Crind, DR MOP, avg customers, avg sales/customer)
       - kitchen product mix (Hot/Cold Grab, Bakery, MTO Food/Coffee, Delivery, Catering, Midax)
       - ending inventory by department (targeted vs actual vs variance)
       - price-override counts (per store)
  3. Runs data-integrity checks (Total = C-Store + Kitchen; YTD sums).
  4. Injects the data into dashboard_template.html (__MONTHLY__ + __EXTRA__) and
     writes the deliverable HTML.

USAGE
  python build_dashboard.py
  (adjust MONTHS for the current period)

This is the HTML half of the monthly automation. See 03_Automation for the full
"drop source files -> fill Excel -> verify -> build outputs" pipeline.
"""
import json, os, glob, warnings
import openpyxl
warnings.filterwarnings("ignore")  # openpyxl data-validation extension warning on the DR file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# NOTE: The monthly workbook holds real business figures and is intentionally NOT
# part of this public repository. In production, place it under data/. For a fully
# runnable, data-free demonstration that needs no workbook, run
# `python sample/generate_sample.py` (it produces demo/dashboard-demo.html).
XLSX = os.path.join(ROOT, "data", "food-sales-variance-report.xlsx")
TPL  = os.path.join(ROOT, "src", "dashboard_template.html")
OUT  = os.path.join(ROOT, "demo", "dashboard.html")
FLAGS = os.path.join(ROOT, "src", "review_flags.json")

def load_flags():
    """Pending 3-month-average review flags -> {sid: {metric: note}} (approved ones excluded)."""
    if not os.path.exists(FLAGS):
        return {}
    try:
        raw = json.load(open(FLAGS, encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for f in raw.values():
        if f.get("status") == "approved":
            continue
        out.setdefault(f["sid"], {})[f["metric"]] = f.get("note", "Flagged for review")
    return out

# store id -> first kitchen-breakdown / ending-inventory row (layout differs slightly per tab)
STORES = [("Cedar Crossing","1001",50),("Maple Junction","1002",50),("Harbor Point","1003",51),("Prairie Gate","1004",51)]
ALL_MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
FOOD_ROW0, SALES_ROW0, CUST_ROW0 = 6, 20, 35           # Jan rows for each block

def _n(v, d=0):
    """Coerce a cell to a number; blanks / #DIV/0! -> default."""
    return v if isinstance(v, (int, float)) else d

MONTH_PREFIX = {"Jan":"JAN","Feb":"FEB","Mar":"MAR","Apr":"APR","May":"MAY","Jun":"JUN",
                "Jul":"JUL","Aug":"AUG","Sep":"SEP","Oct":"OCT","Nov":"NOV","Dec":"DEC"}

def load_overrides(months):
    """Per-store price-override counts, read from the DR Price Override source file
    (numeric site id -> store tab id). This report holds every site, so all
    four store tabs get the section. Returns {sid: [count per month]}, or {}
    if the file isn't found (then the dashboard simply omits the override section)."""
    hits = (glob.glob(os.path.join(ROOT, "data", "sources", "**", "*DR*Price Override*.xlsx"), recursive=True)
            + glob.glob(os.path.join(ROOT, "data", "inbox", "**", "*DR*Price Override*.xlsx"), recursive=True))
    if not hits:
        print("  [note] DR Price Override file not found -> override section skipped")
        return {}
    path = max(hits, key=os.path.getmtime)   # prefer the newest copy (e.g. Aug dropped in the Inbox)
    wb = openpyxl.load_workbook(path, data_only=True)
    def find_sheet(mon):
        pre = MONTH_PREFIX[mon]
        for sn in wb.sheetnames:
            u = sn.upper()
            if u.startswith(pre) and "2026" in u and "2022" not in u:
                return sn
        return None
    out = {sid: [] for _, sid, _ in STORES}
    for mon in months:
        sn = find_sheet(mon); counts = {}
        if sn:
            ws = wb[sn]
            for r in range(1, 40):
                a = ws.cell(r, 1).value
                if isinstance(a, (int, float)):
                    counts[int(a)] = int(_n(ws.cell(r, 2).value))
                if a == "Grand Total":
                    break
        for _, sid, _ in STORES:
            out[sid].append(counts.get(int(sid), 0))   # int(sid) maps the tab id to the numeric site id
    print(f"  Overrides loaded for {len([s for s in out if any(out[s])])}/4 stores from: {os.path.basename(path)}")
    return out

def detect_months(wb):
    """Auto-detect how many months are filled (Total actual, col J of the sales block).
    So when August is entered next month, the dashboard picks it up with no code edit."""
    ws = wb[STORES[0][1]]; last = -1
    for i in range(12):
        if _n(ws.cell(SALES_ROW0+i, 10).value) != 0:
            last = i
    return ALL_MONTHS[:last+1] if last >= 0 else ALL_MONTHS[:1]

def extract():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    MONTHS = detect_months(wb)
    print(f"  Months detected: {MONTHS[0]}-{MONTHS[-1]} ({len(MONTHS)})")
    OVR = load_overrides(MONTHS)     # per-store price-override counts (all four stores)
    data, extra = {}, {}
    for _, sid, kb in STORES:
        ws = wb[sid]; rows = []
        for i in range(len(MONTHS)):
            fr, sr, cr, kr = FOOD_ROW0+i, SALES_ROW0+i, CUST_ROW0+i, kb+i
            rows.append(dict(
                m=MONTHS[i],
                # --- headline / sales (unchanged) ---
                gp_before=round(_n(ws.cell(fr,3).value),4),
                gp_after =round(_n(ws.cell(fr,6).value),4),
                inir     =round(_n(ws.cell(fr,16).value),4),
                shrink   =round(_n(ws.cell(fr,18).value),4),
                sos      =round(_n(ws.cell(fr,19).value),2),
                cstore   =round(_n(ws.cell(sr,4).value)),
                kitchen  =round(_n(ws.cell(sr,7).value)),
                fountain =round(_n(ws.cell(sr,17).value)),
                actual   =round(_n(ws.cell(sr,10).value)),
                budget   =round(_n(ws.cell(sr,9).value)),
                customers=round(_n(ws.cell(cr,3).value)),
                # --- food-margin breakdown ---
                disc_pct =round(_n(ws.cell(fr,4).value),4),   # Discount % of Sales
                disc_d   =round(_n(ws.cell(fr,5).value),2),   # Discount $ Total
                wastage_d=round(_n(ws.cell(fr,7).value),2),   # Wastage $
                sampling_d=round(_n(ws.cell(fr,9).value),2),  # Sampling $ (Free Food)
                spoilage_d=round(_n(ws.cell(fr,11).value),2), # Spoilage $
                logo_d   =round(_n(ws.cell(fr,13).value),2),  # Logo Cups Adjustment $
                shrink_d =round(_n(ws.cell(fr,17).value),2),  # Shrink $
                # --- customer detail ---
                crind    =round(_n(ws.cell(cr,4).value)),     # Crind
                drmop    =round(_n(ws.cell(cr,5).value)),     # DR MOP
                avgcust  =round(_n(ws.cell(cr,8).value)),     # Avg customer # / day
                avgspc   =round(_n(ws.cell(cr,9).value),2),   # Avg sales per customer
                # --- kitchen product mix ---
                hotgrab  =round(_n(ws.cell(kr,3).value),2),
                coldgrab =round(_n(ws.cell(kr,4).value),2),
                bakery   =round(_n(ws.cell(kr,5).value),2),
                mtofood  =round(_n(ws.cell(kr,6).value),2),
                mtocoffee=round(_n(ws.cell(kr,7).value),2),
                delivery =round(_n(ws.cell(kr,8).value),2),
                catering =round(_n(ws.cell(kr,9).value),2),
                midax    =round(_n(ws.cell(kr,10).value),2),
            ))
        data[sid] = rows  # noqa

        # --- ending inventory (current-month snapshot): dept rows kb..kb+10 in cols O/P/Q/R ---
        inv = []
        for r in range(kb, kb+11):
            dept = ws.cell(r,15).value
            if dept in (None, "") or str(dept).strip() in ("Dept.", "Ending Inventory"):
                continue
            inv.append(dict(
                dept=str(dept).strip(),
                targeted=round(_n(ws.cell(r,16).value)),
                ending=round(_n(ws.cell(r,17).value)),
                var=round(_n(ws.cell(r,18).value)),
            ))
        # --- price-override counts (all stores, from the DR Price Override source file) ---
        override = OVR.get(sid) if OVR else None
        extra[sid] = dict(inv=inv, override=override)
    return data, extra, MONTHS

def verify(data):
    ok = True
    for _, sid, _ in STORES:
        for r in data[sid]:
            if abs(r["actual"] - (r["cstore"] + r["kitchen"])) > 1.0:
                print(f"  [WARN] {sid} {r['m']}: Total {r['actual']} != C-Store+Kitchen {r['cstore']+r['kitchen']}")
                ok = False
    grp = sum(sum(r["actual"] for r in data[sid]) for _, sid, _ in STORES)
    print(f"  Group YTD actual = ${grp:,.0f}")
    return ok

def main():
    print("Extracting from:", XLSX)
    data, extra, months = extract()
    print("Verifying data integrity...")
    ok = verify(data)
    print("  Integrity:", "OK" if ok else "CHECK WARNINGS ABOVE")
    html = open(TPL, encoding="utf-8").read()
    flags = load_flags()
    npend = sum(len(v) for v in flags.values())
    print(f"  Review flags pending: {npend}" + (" (values deviate >1.5% from 3-month avg)" if npend else ""))
    html = (html.replace("__MONTHLY__", json.dumps(data))
                .replace("__EXTRA__", json.dumps(extra))
                .replace("__MONS__", json.dumps(months))
                .replace("__FLAGS__", json.dumps(flags)))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("Dashboard written:", OUT)
    print("Bytes:", len(html))

if __name__ == "__main__":
    main()
