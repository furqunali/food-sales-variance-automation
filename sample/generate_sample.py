#!/usr/bin/env python3
"""
generate_sample.py  —  Build a fully runnable DEMO dashboard from synthetic data.

The real monthly workbook (and its source documents) contain confidential business
figures and are NOT part of this public repository. This script fabricates a realistic,
internally-consistent sample dataset for four fictional stores and injects it into the
same production template (src/dashboard_template.html) that the real pipeline uses.

Run it and open the result — no Excel, no source files, no data needed:

    python sample/generate_sample.py
    # -> writes sample/sample_data.json  and  demo/dashboard-demo.html

Everything is deterministic (fixed seed), so the demo is identical on every machine.
The numbers are invented; they resemble real retail-kitchen economics only in shape.
"""
import json, os, random, sys

random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
import analytics  # AI-CFO insight engine (pure, unit-tested)
TPL  = os.path.join(ROOT, "src", "dashboard_template.html")
OUT_JSON = os.path.join(HERE, "sample_data.json")
OUT_HTML = os.path.join(ROOT, "demo", "dashboard-demo.html")

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]

# Four fictional stores, each with a distinct performance profile so the dashboard
# tells a story (one clear leader, one clear laggard) — mirrors real portfolios.
#   name, id, attainment(target actual/budget), monthly base sales, kitchen share
STORES = [
    dict(name="Cedar Crossing", id="1001", attain=0.82, base=185_000, kshare=0.22, inir=0.52, sos=6.6),
    dict(name="Maple Junction", id="1002", attain=0.71, base=150_000, kshare=0.18, inir=0.47, sos=8.1),
    dict(name="Harbor Point",   id="1003", attain=0.75, base=168_000, kshare=0.20, inir=0.49, sos=7.4),
    dict(name="Prairie Gate",   id="1004", attain=0.49, base=132_000, kshare=0.16, inir=0.44, sos=9.8),
]

# Kitchen product-mix proportions (sum = 1.0). One category absorbs the rounding
# remainder so the mix always sums EXACTLY to kitchen sales (verify_sources rule E).
MIX = [
    ("hotgrab", 0.20), ("coldgrab", 0.10), ("bakery", 0.08), ("mtofood", 0.30),
    ("mtocoffee", 0.12), ("delivery", 0.08), ("catering", 0.06), ("midax", 0.06),
]
DEPTS = ["Cigarettes", "Other Tobacco", "Beer", "Soda", "Candy", "Grocery", "General Merch."]


def jitter(base, pct):
    """A small deterministic month-to-month wobble."""
    return base * (1 + random.uniform(-pct, pct))


def build_store(s):
    rows = []
    for i, m in enumerate(MONTHS):
        # gentle seasonal ramp into summer + per-month noise
        season = 1 + 0.03 * i
        cstore = round(jitter(s["base"] * season, 0.05))
        kitchen = round(jitter(s["base"] * s["kshare"] * season, 0.06))
        actual = cstore + kitchen                      # rule: Total = C-Store + Kitchen
        budget = round(actual / jitter(s["attain"], 0.04))
        fountain = round(kitchen * random.uniform(0.05, 0.09))

        gp_before = round(random.uniform(0.56, 0.60), 4)
        disc_pct  = round(random.uniform(0.05, 0.07), 4)
        gp_after  = round(gp_before - disc_pct, 4)
        inir      = round(jitter(s["inir"], 0.03), 4)
        shrink    = round(-random.uniform(0.01, 0.05), 4)

        disc_d     = round(disc_pct * kitchen, 2)
        wastage_d  = round(kitchen * random.uniform(0.010, 0.020), 2)
        sampling_d = round(kitchen * random.uniform(0.003, 0.008), 2)
        spoilage_d = round(kitchen * random.uniform(0.002, 0.006), 2)
        logo_d     = round(kitchen * random.uniform(0.001, 0.003), 2)
        shrink_d   = round(shrink * kitchen, 2)

        customers = round(jitter(actual / random.uniform(11, 14), 0.04))
        crind     = round(customers * random.uniform(0.35, 0.45))
        drmop     = round(customers * random.uniform(0.04, 0.08))
        avgcust   = round(customers / 30)
        avgspc    = round(actual / customers, 2)

        # kitchen product mix — distribute integer dollars, last absorbs remainder
        mix_vals, running = {}, 0
        for k, w in MIX[:-1]:
            v = round(kitchen * w)
            mix_vals[k] = float(v)
            running += v
        mix_vals[MIX[-1][0]] = float(kitchen - running)

        rows.append(dict(
            m=m, gp_before=gp_before, gp_after=gp_after, inir=inir, shrink=shrink,
            sos=round(jitter(s["sos"], 0.05), 2),
            cstore=cstore, kitchen=kitchen, fountain=fountain, actual=actual, budget=budget,
            customers=customers, disc_pct=disc_pct, disc_d=disc_d,
            wastage_d=wastage_d, sampling_d=sampling_d, spoilage_d=spoilage_d,
            logo_d=logo_d, shrink_d=shrink_d, crind=crind, drmop=drmop,
            avgcust=avgcust, avgspc=avgspc, **mix_vals,
        ))
    return rows


def build_extra(s):
    inv = []
    for d in DEPTS:
        targeted = round(random.uniform(8_000, 35_000))
        ending   = round(targeted * random.uniform(0.9, 1.1))
        inv.append(dict(dept=d, targeted=targeted, ending=ending, var=targeted - ending))
    override = [round(jitter(120 * (1.2 if s["attain"] < 0.6 else 0.7), 0.25)) for _ in MONTHS]
    return dict(inv=inv, override=override)


def main():
    data  = {s["id"]: build_store(s) for s in STORES}
    extra = {s["id"]: build_extra(s) for s in STORES}
    flags = {}  # clean demo: everything within trend

    # integrity check (same rule the production verifier enforces)
    for s in STORES:
        for r in data[s["id"]]:
            assert r["actual"] == r["cstore"] + r["kitchen"], "Total must equal C-Store + Kitchen"
            mix = sum(r[k] for k, _ in MIX)
            assert abs(mix - r["kitchen"]) < 1e-6, "Kitchen mix must sum to kitchen sales"

    grp = sum(sum(r["actual"] for r in data[s["id"]]) for s in STORES)
    print(f"  Stores: {len(STORES)}   Months: {MONTHS[0]}-{MONTHS[-1]}   Group YTD actual = ${grp:,.0f}")

    # AI-CFO insights (what changed / why / what to investigate) — same engine the
    # production pipeline uses; deterministic, no LLM.
    store_meta = [dict(id=s["id"], name=s["name"]) for s in STORES]
    insights = analytics.build_insights(MONTHS, data, extra, store_meta)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dict(months=MONTHS, data=data, extra=extra, flags=flags, insights=insights), f, indent=1)
    print("  Wrote sample data:", os.path.relpath(OUT_JSON, ROOT))

    html = open(TPL, encoding="utf-8").read()
    html = (html.replace("__MONTHLY__", json.dumps(data))
                .replace("__EXTRA__",   json.dumps(extra))
                .replace("__MONS__",    json.dumps(MONTHS))
                .replace("__FLAGS__",   json.dumps(flags))
                .replace("__INSIGHTS__", json.dumps(insights)))
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("  Built demo dashboard:", os.path.relpath(OUT_HTML, ROOT), f"({len(html):,} bytes)")
    print("  Open it in any browser — no data, no internet required.")


if __name__ == "__main__":
    main()
