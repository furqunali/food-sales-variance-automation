"""Single-row KPI functions + their behavior on the real sample cells."""
import pytest

import analytics as A
from _data import CELLS, CELL_IDS, DATA


def _row(sid, i):
    return DATA[sid][i]


# --- attainment -------------------------------------------------------------
def test_attainment_on_plan():
    assert A.attainment({"actual": 100, "budget": 100}) == 1.0


def test_attainment_below_plan():
    assert A.attainment({"actual": 80, "budget": 100}) == pytest.approx(0.80)


def test_attainment_above_plan():
    assert A.attainment({"actual": 120, "budget": 100}) == pytest.approx(1.20)


def test_attainment_zero_budget_is_safe():
    assert A.attainment({"actual": 100, "budget": 0}) == 0.0


# --- variance ---------------------------------------------------------------
def test_variance_pct_negative_when_below():
    assert A.variance_pct({"actual": 80, "budget": 100}) == pytest.approx(-0.20)


def test_variance_pct_positive_when_above():
    assert A.variance_pct({"actual": 110, "budget": 100}) == pytest.approx(0.10)


def test_variance_dollars():
    assert A.variance_dollars({"actual": 80, "budget": 100}) == -20


def test_variance_pct_zero_budget_safe():
    assert A.variance_pct({"actual": 5, "budget": 0}) == 0.0


# --- avg ticket -------------------------------------------------------------
def test_avg_ticket():
    assert A.avg_ticket({"actual": 1000, "customers": 100}) == pytest.approx(10.0)


def test_avg_ticket_zero_customers_safe():
    assert A.avg_ticket({"actual": 1000, "customers": 0}) == 0.0


# --- mix shares -------------------------------------------------------------
def test_mix_shares_sum_to_one():
    m = A.mix_shares({"cstore": 60, "kitchen": 30, "fountain": 10})
    assert m["cstore"] == pytest.approx(0.6)
    assert sum(m.values()) == pytest.approx(1.0)


def test_mix_shares_empty_safe():
    m = A.mix_shares({"cstore": 0, "kitchen": 0, "fountain": 0})
    assert sum(m.values()) == 0.0


# --- parametrized over EVERY real sample cell -------------------------------
@pytest.mark.parametrize("sid,i", CELLS, ids=CELL_IDS)
def test_cell_total_equals_cstore_plus_kitchen(sid, i):
    r = _row(sid, i)
    assert abs(r["actual"] - (r["cstore"] + r["kitchen"])) < 1e-6


@pytest.mark.parametrize("sid,i", CELLS, ids=CELL_IDS)
def test_cell_attainment_in_business_range(sid, i):
    a = A.attainment(_row(sid, i))
    assert 0.2 < a < 1.6                        # realistic monthly attainment band


@pytest.mark.parametrize("sid,i", CELLS, ids=CELL_IDS)
def test_cell_avg_ticket_positive(sid, i):
    assert A.avg_ticket(_row(sid, i)) > 0


@pytest.mark.parametrize("sid,i", CELLS, ids=CELL_IDS)
def test_cell_variance_pct_matches_attainment(sid, i):
    r = _row(sid, i)
    assert A.variance_pct(r) == pytest.approx(A.attainment(r) - 1.0)
