"""explain_store / explain_group / build_insights — the reviewer-facing narrative."""
import pytest

import analytics as A
from _data import DATA, STORES, STORE_IDS


def test_explain_store_has_full_shape():
    node = A.explain_store("Cedar Crossing", "1001", DATA["1001"])
    for key in ("headline", "revenue_change_pct", "drivers", "risks",
                "recommendations", "ytd_attainment", "month_attainment"):
        assert key in node


def test_explain_store_headline_mentions_name():
    node = A.explain_store("Cedar Crossing", "1001", DATA["1001"])
    assert "Cedar Crossing" in node["headline"]


def test_explain_store_short_history_is_graceful():
    node = A.explain_store("X", "9", [{"actual": 100, "budget": 120, "customers": 10,
                                       "cstore": 70, "kitchen": 30}])
    assert node["drivers"] == [] and node["recommendations"] == []
    assert "Insufficient" in node["headline"]


def test_explain_group_shape_and_ordering():
    g = A.explain_group(STORES, DATA)
    assert g["best_store"]["attainment"] >= g["worst_store"]["attainment"]
    assert "Group at" in g["headline"]
    assert g["gap_dollars"] == pytest.approx(g["ytd_budget"] - g["ytd_actual"])


def test_build_insights_structure():
    ins = A.build_insights([], DATA, stores=STORES)
    assert set(ins.keys()) == {"group", "stores"}
    assert len(ins["stores"]) == len(STORES)


def test_build_insights_defaults_stores_from_data():
    ins = A.build_insights([], DATA)
    assert len(ins["stores"]) == len(DATA)


@pytest.mark.parametrize("sid", STORE_IDS)
def test_each_store_narrative_reports_attainment_pct(sid):
    name = next(s["name"] for s in STORES if s["id"] == sid)
    node = A.explain_store(name, sid, DATA[sid])
    assert 0.0 < node["ytd_attainment"] < 1.6


@pytest.mark.parametrize("sid", STORE_IDS)
def test_each_store_revenue_change_is_a_fraction(sid):
    name = next(s["name"] for s in STORES if s["id"] == sid)
    node = A.explain_store(name, sid, DATA[sid])
    assert -1.0 < node["revenue_change_pct"] < 1.0
