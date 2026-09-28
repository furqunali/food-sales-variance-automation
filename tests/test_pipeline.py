from datetime import date

from food_variance.pipeline import analyze_period


def test_analyze_period_uses_canonical_variance_engine():
    result = analyze_period("store-1", date(2026, 9, 1), 850, 150)
    assert result.sales_variance == 1000
    assert result.reconciliation_ok is True
