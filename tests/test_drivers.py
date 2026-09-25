"""Driver decomposition, margin risks, recommendations — the AI-CFO 'why'."""
import pytest

import analytics as A
from _data import DATA, STORE_IDS


PREV = {"actual": 1000, "budget": 1200, "customers": 100, "cstore": 700, "kitchen": 300,
        "fountain": 20, "gp_after": 0.52, "inir": 0.50, "shrink": -0.02, "disc_pct": 0.06}
CUR_DOWN = {"actual": 880, "budget": 1200, "customers": 92, "cstore": 620, "kitchen": 260,
            "fountain": 18, "gp_after": 0.49, "inir": 0.47, "shrink": -0.05, "disc_pct": 0.09}


def test_pct_change_basic():
    assert A.pct_change(110, 100) == pytest.approx(0.10)
    assert A.pct_change(90, 100) == pytest.approx(-0.10)
    assert A.pct_change(5, 0) == 0.0


def test_customer_and_ticket_effects_sum_to_revenue_change():
    d = {x["key"]: x["dollars"] for x in A.revenue_drivers(CUR_DOWN, PREV)}
    total = d["customers"] + d["avg_ticket"]
    assert total == pytest.approx(CUR_DOWN["actual"] - PREV["actual"])


def test_channel_effects_sum_to_revenue_change():
    d = {x["key"]: x["dollars"] for x in A.revenue_drivers(CUR_DOWN, PREV)}
    assert d["cstore"] + d["kitchen"] == pytest.approx(CUR_DOWN["actual"] - PREV["actual"])


def test_drivers_sorted_by_absolute_impact():
    ds = A.revenue_drivers(CUR_DOWN, PREV)
    mags = [abs(x["dollars"]) for x in ds]
    assert mags == sorted(mags, reverse=True)


def test_drivers_all_negative_when_everything_falls():
    for x in A.revenue_drivers(CUR_DOWN, PREV):
        assert x["dollars"] <= 0


def test_margin_risks_flag_falling_gp_and_inir():
    keys = {r["key"] for r in A.margin_risks(CUR_DOWN, PREV)}
    assert "gp_after" in keys and "inir" in keys


def test_margin_risks_flag_worsening_shrink_and_discount():
    keys = {r["key"] for r in A.margin_risks(CUR_DOWN, PREV)}
    assert "shrink" in keys and "disc_pct" in keys


def test_margin_risks_empty_when_stable():
    assert A.margin_risks(PREV, PREV) == []


def test_recommendations_mention_traffic_and_food_cost():
    recs = " ".join(A.recommendations(A.revenue_drivers(CUR_DOWN, PREV),
                                      A.margin_risks(CUR_DOWN, PREV))).lower()
    assert "traffic" in recs or "footfall" in recs
    assert "food cost" in recs


def test_recommendations_empty_when_no_issues():
    assert A.recommendations(A.revenue_drivers(PREV, PREV), A.margin_risks(PREV, PREV)) == []


@pytest.mark.parametrize("sid", STORE_IDS)
def test_revenue_drivers_decomposition_holds_on_sample(sid):
    rows = DATA[sid]
    cur, prev = rows[-1], rows[-2]
    d = {x["key"]: x["dollars"] for x in A.revenue_drivers(cur, prev)}
    assert d["customers"] + d["avg_ticket"] == pytest.approx(cur["actual"] - prev["actual"], rel=1e-6)
    assert d["cstore"] + d["kitchen"] == pytest.approx(cur["actual"] - prev["actual"], rel=1e-6)
