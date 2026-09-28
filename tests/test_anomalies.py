"""detect_anomalies — the month-over-month integrity + swing checker."""
import pytest

import analytics as A
from _data import DATA, STORES, STORE_IDS


CLEAN = [
    {"m": "Jan", "actual": 100, "cstore": 70, "kitchen": 30, "inir": 0.50, "gp_before": 0.58, "shrink": -0.02},
    {"m": "Feb", "actual": 105, "cstore": 73, "kitchen": 32, "inir": 0.51, "gp_before": 0.58, "shrink": -0.02},
]


def test_clean_series_has_no_flags():
    assert A.detect_anomalies(CLEAN, "Store", "1") == []


def test_integrity_break_is_flagged():
    bad = [dict(CLEAN[0]), {"m": "Feb", "actual": 200, "cstore": 70, "kitchen": 30}]
    flags = A.detect_anomalies(bad, "Store", "1")
    assert any("Total" in f for f in flags)


def test_large_sales_swing_is_flagged():
    swing = [dict(CLEAN[0]), {"m": "Feb", "actual": 130, "cstore": 91, "kitchen": 39}]
    flags = A.detect_anomalies(swing, "Store", "1")
    assert any("sales moved" in f for f in flags)


def test_margin_swing_is_flagged():
    ms = [dict(CLEAN[0]),
          {"m": "Feb", "actual": 105, "cstore": 73, "kitchen": 32, "inir": 0.40, "gp_before": 0.58, "shrink": -0.02}]
    flags = A.detect_anomalies(ms, "Store", "1")
    assert any("INIR" in f for f in flags)


def test_small_moves_not_flagged():
    ok = [dict(CLEAN[0]),
          {"m": "Feb", "actual": 108, "cstore": 75, "kitchen": 33, "inir": 0.52, "gp_before": 0.58, "shrink": -0.02}]
    assert A.detect_anomalies(ok, "Store", "1") == []


@pytest.mark.parametrize("sid", STORE_IDS)
def test_sample_stores_have_consistent_totals(sid):
    # the sample dataset is internally consistent -> no integrity ('Total') flags
    name = next(s["name"] for s in STORES if s["id"] == sid)
    flags = A.detect_anomalies(DATA[sid], name, sid)
    assert not any("Total" in f for f in flags)
