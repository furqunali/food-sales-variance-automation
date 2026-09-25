#!/usr/bin/env python3
"""
analytics.py  —  The AI-CFO / Finance Analytics engine.

Pure, dependency-free functions that turn the monthly store figures into
**business KPIs (with %)** and, more importantly, into a plain-language
explanation a CFO actually wants:

    What changed?  →  Why (which drivers)?  →  What's the risk?  →  What to investigate?

Every conclusion is derived deterministically from the numbers (and carries the
numbers with it), so it is auditable and fully unit-tested — no LLM, no guessing.

Data shapes (same as sample/sample_data.json and the production pipeline):
    months : ["Jan", "Feb", ...]
    data   : { store_id: [ {m, actual, budget, cstore, kitchen, fountain,
                            customers, gp_before, gp_after, inir, shrink,
                            disc_pct, sos, ...}, ... ] }
    stores : [ {"id": "1001", "name": "Cedar Crossing"}, ... ]
"""
from __future__ import annotations

# --- thresholds (business-tunable) ------------------------------------------
MATERIAL_PCT = 0.03          # a sales move is "material" at >= 3%
MARGIN_PT = 0.02             # a margin move (GP%/INIR) matters at >= 2 points
SALES_SWING = 0.15           # anomaly: month-over-month sales swing > 15%
MARGIN_SWING = 0.05          # anomaly: margin/GP%/shrink swing > 5 points


# --- single-row KPIs --------------------------------------------------------
def attainment(row) -> float:
    """Budget attainment = actual / budget (1.0 = on plan)."""
    b = row.get("budget") or 0
    return (row["actual"] / b) if b else 0.0


def variance_pct(row) -> float:
    """Signed variance vs budget as a fraction (negative = below plan)."""
    b = row.get("budget") or 0
    return ((row["actual"] - b) / b) if b else 0.0


def variance_dollars(row) -> float:
    return row["actual"] - (row.get("budget") or 0)


def avg_ticket(row) -> float:
    """Average sales per customer (a.k.a. average basket)."""
    c = row.get("customers") or 0
    return (row["actual"] / c) if c else 0.0


def mix_shares(row) -> dict:
    """C-Store / Kitchen / Fountain as a share of total sales."""
    total = (row.get("cstore", 0) + row.get("kitchen", 0) + row.get("fountain", 0)) or 0
    if not total:
        return {"cstore": 0.0, "kitchen": 0.0, "fountain": 0.0}
    return {
        "cstore": row.get("cstore", 0) / total,
        "kitchen": row.get("kitchen", 0) / total,
        "fountain": row.get("fountain", 0) / total,
    }


# --- YTD / group rollups ----------------------------------------------------
_SUM_FIELDS = ("actual", "budget", "cstore", "kitchen", "fountain", "customers")


def ytd(rows) -> dict:
    """Sum the additive fields across all supplied months + derived KPIs."""
    out = {f: sum(r.get(f, 0) for r in rows) for f in _SUM_FIELDS}
    out["attainment"] = attainment(out)
    out["variance_pct"] = variance_pct(out)
    out["variance_dollars"] = variance_dollars(out)
    out["avg_ticket"] = avg_ticket(out)
    return out


def group_ytd(data) -> dict:
    """YTD rollup across every store."""
    all_rows = [r for rows in data.values() for r in rows]
    return ytd(all_rows)


def rank_by_attainment(data, stores) -> list:
    """Stores ranked best→worst by YTD attainment: [{id, name, attainment}]."""
    ranked = []
    for s in stores:
        y = ytd(data[s["id"]])
        ranked.append({"id": s["id"], "name": s.get("name", s["id"]), "attainment": y["attainment"]})
    ranked.sort(key=lambda x: x["attainment"], reverse=True)
    return ranked


# --- change / driver decomposition -----------------------------------------
def pct_change(cur: float, prev: float) -> float:
    return ((cur - prev) / prev) if prev else 0.0


def revenue_drivers(cur, prev) -> list:
    """Decompose the month-over-month revenue change into exact, additive effects.

    Revenue = customers × avg_ticket, so
        Δrev = (Δcustomers · avg_ticket_prev) + (Δavg_ticket · customers_cur)
    (these two terms sum exactly to Δrevenue). Also split by channel
    (C-Store vs Kitchen), which likewise sums to Δrevenue.
    Returns drivers sorted by absolute dollar impact.
    """
    t_prev, t_cur = avg_ticket(prev), avg_ticket(cur)
    c_prev, c_cur = prev.get("customers", 0), cur.get("customers", 0)
    customer_effect = (c_cur - c_prev) * t_prev
    ticket_effect = (t_cur - t_prev) * c_cur

    cstore_effect = cur.get("cstore", 0) - prev.get("cstore", 0)
    kitchen_effect = cur.get("kitchen", 0) - prev.get("kitchen", 0)

    drivers = [
        {"key": "customers", "label": "Customer count", "dollars": customer_effect,
         "pct": pct_change(c_cur, c_prev)},
        {"key": "avg_ticket", "label": "Average ticket", "dollars": ticket_effect,
         "pct": pct_change(t_cur, t_prev)},
        {"key": "cstore", "label": "C-Store sales", "dollars": cstore_effect,
         "pct": pct_change(cur.get("cstore", 0), prev.get("cstore", 0))},
        {"key": "kitchen", "label": "Kitchen sales", "dollars": kitchen_effect,
         "pct": pct_change(cur.get("kitchen", 0), prev.get("kitchen", 0))},
    ]
    drivers.sort(key=lambda d: abs(d["dollars"]), reverse=True)
    return drivers


def margin_risks(cur, prev) -> list:
    """Point-change risks in margins/food cost. Returns list of {label, delta_pts, note}."""
    risks = []
    checks = [
        ("gp_after", "GP% after discount"),
        ("inir", "Kitchen INIR (net food margin)"),
    ]
    for key, label in checks:
        if key in cur and key in prev:
            delta = cur[key] - prev[key]
            if delta <= -MARGIN_PT:
                risks.append({"key": key, "label": label, "delta_pts": delta,
                              "note": f"{label} fell {abs(delta) * 100:.1f} pts"})
    # shrink is negative; more negative = worse
    if "shrink" in cur and "shrink" in prev and (cur["shrink"] - prev["shrink"]) <= -MARGIN_PT:
        risks.append({"key": "shrink", "label": "Shrink", "delta_pts": cur["shrink"] - prev["shrink"],
                      "note": f"Shrink worsened {abs(cur['shrink'] - prev['shrink']) * 100:.1f} pts"})
    # discount rate rising eats margin
    if "disc_pct" in cur and "disc_pct" in prev and (cur["disc_pct"] - prev["disc_pct"]) >= MARGIN_PT:
        risks.append({"key": "disc_pct", "label": "Discount rate", "delta_pts": cur["disc_pct"] - prev["disc_pct"],
                      "note": f"Discount rate rose {(cur['disc_pct'] - prev['disc_pct']) * 100:.1f} pts"})
    return risks


def recommendations(drivers, risks) -> list:
    """Turn the top drivers + risks into concrete 'what to investigate' actions."""
    recs = []
    neg = [d for d in drivers if d["dollars"] < 0]
    neg.sort(key=lambda d: d["dollars"])  # most negative first
    for d in neg[:2]:
        if d["key"] == "customers":
            recs.append(f"Investigate traffic/footfall — customer count {d['pct'] * 100:+.1f}%.")
        elif d["key"] == "avg_ticket":
            recs.append(f"Review pricing, basket size and discounting — average ticket {d['pct'] * 100:+.1f}%.")
        elif d["key"] == "kitchen":
            recs.append(f"Check kitchen product mix / MTO throughput — kitchen sales {d['pct'] * 100:+.1f}%.")
        elif d["key"] == "cstore":
            recs.append(f"Review C-Store category performance — C-Store sales {d['pct'] * 100:+.1f}%.")
    for r in risks:
        if r["key"] in ("inir", "gp_after"):
            recs.append("Review food cost, supplier pricing and waste — " + r["note"].lower() + ".")
        elif r["key"] == "shrink":
            recs.append("Audit inventory shrink and cash handling — " + r["note"].lower() + ".")
        elif r["key"] == "disc_pct":
            recs.append("Tighten discount authorization — " + r["note"].lower() + ".")
    return recs


# --- narrative per store / group -------------------------------------------
def explain_store(name, sid, rows) -> dict:
    """Latest-month narrative for one store (needs >= 2 months of data)."""
    y = ytd(rows)
    node = {"id": sid, "name": name,
            "ytd_attainment": y["attainment"], "ytd_variance_pct": y["variance_pct"],
            "ytd_actual": y["actual"], "ytd_budget": y["budget"]}
    if len(rows) < 2:
        node.update(headline="Insufficient history for a month-over-month explanation.",
                    revenue_change_pct=0.0, drivers=[], risks=[], recommendations=[])
        return node
    cur, prev = rows[-1], rows[-2]
    rev_pct = pct_change(cur["actual"], prev["actual"])
    drivers = revenue_drivers(cur, prev)
    risks = margin_risks(cur, prev)
    direction = "up" if rev_pct >= 0 else "down"
    node.update(
        month=cur.get("m"), prev_month=prev.get("m"),
        revenue_change_pct=rev_pct,
        month_attainment=attainment(cur), month_variance_pct=variance_pct(cur),
        headline=f"{name}: revenue {direction} {abs(rev_pct) * 100:.1f}% vs {prev.get('m')} "
                 f"(attainment {attainment(cur) * 100:.0f}% of budget).",
        drivers=drivers, risks=risks, recommendations=recommendations(drivers, risks),
    )
    return node


def explain_group(stores, data) -> dict:
    g = group_ytd(data)
    ranked = rank_by_attainment(data, stores)
    best, worst = ranked[0], ranked[-1]
    return {
        "ytd_attainment": g["attainment"], "ytd_variance_pct": g["variance_pct"],
        "ytd_actual": g["actual"], "ytd_budget": g["budget"],
        "gap_dollars": -g["variance_dollars"],
        "best_store": best, "worst_store": worst,
        "headline": f"Group at {g['attainment'] * 100:.1f}% of budget YTD "
                    f"({g['variance_pct'] * 100:+.1f}%). "
                    f"{best['name']} leads at {best['attainment'] * 100:.0f}%; "
                    f"{worst['name']} trails at {worst['attainment'] * 100:.0f}%.",
    }


def build_insights(months, data, extra=None, stores=None) -> dict:
    """The full AI-CFO payload the dashboard renders (and the pipeline injects)."""
    if stores is None:
        stores = [{"id": sid, "name": sid} for sid in data]
    return {
        "group": explain_group(stores, data),
        "stores": [explain_store(s.get("name", s["id"]), s["id"], data[s["id"]]) for s in stores],
    }


# --- anomaly detection (JSON port of verify_month) --------------------------
def detect_anomalies(rows, name=None, sid=None) -> list:
    """Month-over-month integrity + swing checks on a store's rows.

    Flags: Total != C-Store + Kitchen; sales swing > 15%; GP%/INIR/shrink swing
    > 5 points. Returns a list of human-readable strings (empty = clean).
    """
    flags = []
    tag = f"{name or ''} {sid or ''}".strip()
    for i, r in enumerate(rows):
        # internal consistency
        if abs(r["actual"] - (r.get("cstore", 0) + r.get("kitchen", 0))) > 1.0:
            flags.append(f"{tag} {r.get('m', i)}: Total {r['actual']:,.0f} != C-Store+Kitchen")
        if i == 0:
            continue
        prev = rows[i - 1]
        if prev["actual"] and abs(pct_change(r["actual"], prev["actual"])) > SALES_SWING:
            flags.append(f"{tag} {r.get('m', i)}: sales moved "
                         f"{pct_change(r['actual'], prev['actual']) * 100:+.0f}% vs {prev.get('m')}")
        for key, label in (("inir", "INIR"), ("gp_before", "GP% before"), ("shrink", "Shrink")):
            if key in r and key in prev and abs(r[key] - prev[key]) > MARGIN_SWING:
                flags.append(f"{tag} {r.get('m', i)}: {label} moved "
                             f"{(r[key] - prev[key]) * 100:+.1f} pts vs {prev.get('m')}")
    return flags
