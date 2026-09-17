from datetime import date

import pytest

from src.food_variance.calculator import calculate_variance
from src.food_variance.models import StoreSnapshot


def snapshot(**kwargs):
    defaults = dict(
        store_id="1001",
        store_name="Cedar Crossing",
        period=date(2026, 1, 1),
        kitchen_sales=1000,
        cstore_sales=500,
        gp_before=0.30,
        gp_after=0.28,
        product_mix={"hotgrab": 500, "coldgrab": 500},
    )
    defaults.update(kwargs)
    return StoreSnapshot(**defaults)


def test_reconciles_product_mix():
    result = calculate_variance(snapshot())
    assert result.reconciliation_ok
    assert result.mix_variance == 0


def test_detects_mix_mismatch():
    result = calculate_variance(snapshot(product_mix={"hotgrab": 700}))
    assert not result.reconciliation_ok
    assert "product mix" in result.warnings[0]


def test_compares_baseline():
    current = snapshot(kitchen_sales=1200, cstore_sales=600)
    baseline = snapshot(kitchen_sales=1000, cstore_sales=500)
    result = calculate_variance(current, baseline)
    assert result.sales_variance == 300


def test_rejects_negative_tolerance():
    with pytest.raises(ValueError):
        calculate_variance(snapshot(), tolerance=-1)
