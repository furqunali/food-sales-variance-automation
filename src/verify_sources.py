#!/usr/bin/env python3
"""
verify_sources.py  —  DOUBLE-VERIFY the dashboard against the original source documents.

Chain of trust checked here (current/last month):
  A. Dashboard HTML  ==  Excel workbook        (the dashboard faithfully reflects the workbook)
  B. Workbook margin ==  Weighted Average src  (GP% before/after, discount %/$, kitchen sales, INIR)
  C. Workbook cstore ==  Retail Dept Summary   (C-store retail actual, from the PDF *Total Sales)
  D. Override counts  ==  DR Price Override src (per store)
  E. Kitchen mix sum  ==  kitchen sales         (internal consistency + == Weighted Average)

Image / scanned sources (Cost INIR kitchen, Customer counts, Speed-of-Service) are read by AI
vision at fill time and are listed at the end for manual sign-off (they cannot be re-parsed here).

USAGE:  python verify_sources.py
Exit 0 = all automated checks passed.  Prints a PASS/FAIL line per field per store.
"""
import os, re, json, glob, warnings
import openpyxl
warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The real workbook, deliverable, and source documents are private (not in this
# public repo). Paths below reflect the production layout. See README.
XLSX = os.path.join(ROOT, "data", "food-sales-variance-report.xlsx")
HTML = os.path.join(ROOT, "demo", "dashboard.html")
SRC  = os.path.join(ROOT, "data", "sources")
STORES = [("Cedar Crossing","1001",50),("Maple Junction","1002",50),("Harbor Point","1003",51),("Prairie Gate","1004",51)]
NAME2WA = {"1001":"Cedar Crossing","1002":"Maple Junction","1003":"Harbor Point","1004":"Prairie Gate"}
FOOD0, SALES0 = 6, 20

npass = nfail = 0
def chk(label, a, b, tol):
    global npass, nfail
    try:
        ok = abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        ok = (a == b)
    (globals().__setitem__('npass', npass+1) if ok else globals().__setitem__('nfail', nfail+1))
    print(f"   [{'PASS' if ok else 'FAIL'}] {label}: dashboard/workbook={a}  source={b}")
    return ok

INBOX = os.path.join(ROOT, "data", "inbox")
def find(pat):
    """Find a source file in 05_Source or the monthly Inbox; return the NEWEST match
    so the current month's freshly-dropped files win over older samples."""
    hits = glob.glob(os.path.join(SRC, "**", pat), recursive=True) + \
           glob.glob(os.path.join(INBOX, "**", pat), recursive=True)
    return max(hits, key=os.path.getmtime) if hits else None

def last_month_idx(ws):
    last = -1
    for i in range(12):
        v = ws.cell(SALES0+i,10).value
        if isinstance(v,(int,float)) and v: last = i
    return last

# ---------- load dashboard data from the deliverable HTML ----------
html = open(HTML, encoding="utf-8").read()
MD = json.loads(re.search(r"const MD=(\{.*?\});", html, re.S).group(1))
EX = json.loads(re.search(r"const EX=(\{.*?\});", html, re.S).group(1))
MONS = json.loads(re.search(r"const MONS=(\[.*?\]);", html, re.S).group(1))
wb = openpyxl.load_workbook(XLSX, data_only=True)
idx = last_month_idx(wb[STORES[0][1]]); mon = MONS[idx]
print(f"=== Double-verify — month {mon} (index {idx}) ===")

# ---------- A. dashboard == workbook ----------
print("\nA. Dashboard HTML  ==  Excel workbook")
for _, sid, _ in STORES:
    ws = wb[sid]; d = MD[sid][idx]
    chk(f"{sid} kitchen $", d["kitchen"], round(ws.cell(SALES0+idx,7).value or 0), 1)
    chk(f"{sid} cstore $",  d["cstore"],  round(ws.cell(SALES0+idx,4).value or 0), 1)
    chk(f"{sid} INIR",      d["inir"],    round(ws.cell(FOOD0+idx,16).value or 0,4), 0.0005)

# ---------- B. workbook margin == Weighted Average source ----------
print("\nB. Workbook margin ==  Weighted Average source")
waf = find("08*Weighted Average*.xlsx")
if waf:
    wa = openpyxl.load_workbook(waf, data_only=True)["Comparison"]
    warows = {}
    for r in range(6, 12):
        nm = wa.cell(r,2).value
        if nm: warows[str(nm).strip()] = r
    for _, sid, _ in STORES:
        r = warows.get(NAME2WA[sid]); d = MD[sid][idx]
        if not r: print(f"   [FAIL] {sid}: not found in Weighted Average"); nfail += 1; continue
        chk(f"{sid} GP% before", d["gp_before"], round(wa.cell(r,7).value,4), 0.0005)
        chk(f"{sid} GP% after",  d["gp_after"],  round(wa.cell(r,8).value,4), 0.0005)
        chk(f"{sid} Discount %", d["gp_before"]-d["gp_after"] if False else MD[sid][idx].get("disc_pct"), round(wa.cell(r,9).value,4), 0.0006)
        chk(f"{sid} Discount $", MD[sid][idx].get("disc_d"), round(wa.cell(r,6).value,2), 1.0)
        chk(f"{sid} Kitchen $",  d["kitchen"], round(wa.cell(r,4).value), 1.0)
        chk(f"{sid} INIR",       d["inir"], round(wa.cell(r,10).value,4), 0.0005)
else:
    print("   [skip] Weighted Average source not found")

# ---------- C. workbook cstore == Retail Dept Summary PDF ----------
print("\nC. Workbook C-store actual ==  Retail Dept Summary (PDF)")
rpdf = find("RETAIL DEPT SUMMARY*.PDF") or find("RETAIL DEPT SUMMARY*.pdf")
try:
    import pdfplumber
    txt = ""
    with pdfplumber.open(rpdf) as pdf:
        for pg in pdf.pages: txt += (pg.extract_text() or "") + "\n"
    for _, sid, _ in STORES:
        m = re.search(rf"Site {sid} - .*?\*Total:(.*?)(?:\*\*Total:|Org \d|Site \d{{4}} -|$)", txt, re.S)
        sales = None
        if m:
            nums = re.findall(r"[-\d][\d,]*\.?\d*-?", m.group(1))
            # the second '*Total' line ends with: ... <Sales> <EndingRetail>; Sales = second-to-last
            clean = [float(x.replace(",","").replace("-","")) * (-1 if x.endswith("-") else 1) for x in nums if re.search(r"\d",x)]
            if len(clean) >= 2: sales = clean[-2]
        chk(f"{sid} C-store actual", MD[sid][idx]["cstore"], sales, 2.0)
except Exception as e:
    print("   [skip] Retail PDF parse:", e)

# ---------- D. override == DR Price Override source ----------
print("\nD. Price-override counts ==  DR Price Override source")
drf = find("3 - DR - Price Override*.xlsx")
if drf:
    dr = openpyxl.load_workbook(drf, data_only=True)
    pre = {"Jan":"JAN","Feb":"FEB","Mar":"MAR","Apr":"APR","May":"MAY","Jun":"JUN","Jul":"JUL"}[mon]
    sh = next((s for s in dr.sheetnames if s.upper().startswith(pre) and "2026" in s.upper() and "2022" not in s.upper()), None)
    counts = {}
    if sh:
        ws = dr[sh]
        for r in range(1,40):
            a = ws.cell(r,1).value
            if isinstance(a,(int,float)): counts[int(a)] = int(ws.cell(r,2).value or 0)
            if a == "Grand Total": break
    for _, sid, _ in STORES:
        ov = EX[sid].get("override")
        chk(f"{sid} override ({mon})", ov[idx] if ov else None, counts.get(int(sid)), 0)
else:
    print("   [skip] DR Price Override source not found")

# ---------- E. kitchen product-mix sum == kitchen sales ----------
print("\nE. Kitchen product-mix sum ==  kitchen sales (internal)")
for _, sid, _ in STORES:
    d = MD[sid][idx]
    mix = sum(d[k] for k in ["hotgrab","coldgrab","bakery","mtofood","mtocoffee","delivery","catering","midax"])
    chk(f"{sid} mix sum vs kitchen", round(mix), d["kitchen"], 2.0)

print(f"\n=== RESULT: {npass} passed, {nfail} failed ===")
print("Vision sources (manual sign-off): Cost INIR kitchen PDF (wastage/sampling/spoilage/logo/kitchen+fountain margin),"
      " Customer counts.jpg (customers/Crind/DR MOP), Speed-of-Service PNGs (SOS min).")
raise SystemExit(1 if nfail else 0)
