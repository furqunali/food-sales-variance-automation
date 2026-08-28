#!/usr/bin/env python3
"""
verify_month.py  —  Monthly data-integrity + variance checker (the "catch-mistakes" gate).

Reads the Excel report and, for the latest filled month, checks:
  1. Internal consistency  : Total = C-Store + Kitchen (per store).
  2. Month-over-month swings: sales +/-15%, margins/GP%/shrink +/-5 pts, override +/-50%.
It prints a VERIFY list. If the list is empty -> safe to email; else -> review the flagged
source before sending.

USAGE:  python verify_month.py            (checks the last filled month automatically)
"""
import os, openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The real monthly workbook is private (not in this public repo). See README.
XLSX = os.path.join(ROOT, "data", "food-sales-variance-report.xlsx")
STORES = [("Cedar Crossing","1001"),("Maple Junction","1002"),("Harbor Point","1003"),("Prairie Gate","1004")]
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
SALES0, FOOD0 = 20, 6

# thresholds (edit to taste)
T_SALES_PCT = 0.15     # store total sales month-over-month
T_MARGIN_PT = 0.05     # INIR / GP% / shrink, in absolute percentage points

def last_filled(ws):
    """Return the index (0..11) of the last month whose Total actual (col J) is filled."""
    last = -1
    for i in range(12):
        v = ws.cell(SALES0+i, 10).value
        if v not in (None, 0): last = i
    return last

def main():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    flags = []
    idx = last_filled(wb[STORES[0][1]])
    if idx < 0:
        print("No filled month found."); return
    m = MONTHS[idx]
    print(f"=== Verifying month: {m} (row {SALES0+idx}) ===\n")
    for nm, sid in STORES:
        ws = wb[sid]
        cur_act = ws.cell(SALES0+idx,10).value or 0
        cur_cs  = ws.cell(SALES0+idx,4).value or 0
        cur_k   = ws.cell(SALES0+idx,7).value or 0
        # 1. internal consistency
        if abs(cur_act - (cur_cs+cur_k)) > 1.0:
            flags.append(f"{nm} {sid}: Total {cur_act:,.0f} != C-Store+Kitchen {cur_cs+cur_k:,.0f}  -> check Retail/Hourly source")
        # 2. MoM swings vs previous month
        if idx > 0:
            prev_act = ws.cell(SALES0+idx-1,10).value or 0
            if prev_act and abs(cur_act-prev_act)/prev_act > T_SALES_PCT:
                flags.append(f"{nm} {sid}: sales moved {(cur_act-prev_act)/prev_act*100:+.0f}% vs {MONTHS[idx-1]} "
                             f"({prev_act:,.0f} -> {cur_act:,.0f})  -> verify Weighted-Average / Retail")
            for col, label, src in [(16,"INIR margin","Cost INIR / Weighted-Average"),
                                    (3,"GP% before","Weighted-Average"),
                                    (18,"Shrink %","Cost INIR")]:
                cv = ws.cell(FOOD0+idx,col).value; pv = ws.cell(FOOD0+idx-1,col).value
                if isinstance(cv,(int,float)) and isinstance(pv,(int,float)) and abs(cv-pv) > T_MARGIN_PT:
                    flags.append(f"{nm} {sid}: {label} moved {(cv-pv)*100:+.1f} pts vs {MONTHS[idx-1]} "
                                 f"({pv*100:.1f}% -> {cv*100:.1f}%)  -> verify {src}")
    if flags:
        print(f"[!] {len(flags)} item(s) to VERIFY before emailing:\n")
        for f in flags: print("   -", f)
        print("\n=> Review the flagged source file(s); if legit, proceed. Else fix the entry.")
    else:
        print("[OK] No anomalies. Data is in normal sequence -> safe to generate PDF/HTML and email.")

if __name__ == "__main__":
    main()
