"""YTD / group rollups and ranking."""
import pytest

import analytics as A
from _data import DATA, STORES, STORE_IDS


ROWS = [
    {"actual": 100, "budget": 120, "cstore": 70, "kitchen": 30, "fountain": 2, "customers": 10},
    {"actual": 110, "budget": 120, "cstore": 76, "kitchen": 34, "fountain": 3, "customers": 11},
]


def test_ytd_sums_additive_fields():
    y = A.ytd(ROWS)
    assert y["actual"] == 210
    assert y["budget"] == 240
    assert y["customers"] == 21


def test_ytd_derived_kpis():
    y = A.ytd(ROWS)
    assert y["attainment"] == pytest.approx(210 / 240)
    assert y["variance_dollars"] == -30
    assert y["avg_ticket"] == pytest.approx(210 / 21)


def test_group_ytd_matches_sum_of_stores(data):
    g = A.group_ytd(data)
    assert g["actual"] == sum(A.ytd(rows)["actual"] for rows in data.values())


def test_rank_by_attainment_is_descending():
    ranked = A.rank_by_attainment(DATA, STORES)
    atts = [r["attainment"] for r in ranked]
    assert atts == sorted(atts, reverse=True)


def test_rank_has_every_store():
    ranked = A.rank_by_attainment(DATA, STORES)
    assert {r["id"] for r in ranked} == set(STORE_IDS)


@pytest.mark.parametrize("sid", STORE_IDS)
def test_store_ytd_attainment_positive(sid):
    assert A.ytd(DATA[sid])["attainment"] > 0


@pytest.mark.parametrize("sid", STORE_IDS)
def test_store_ytd_variance_matches_attainment(sid):
    y = A.ytd(DATA[sid])
    assert y["variance_pct"] == pytest.approx(y["attainment"] - 1.0)
