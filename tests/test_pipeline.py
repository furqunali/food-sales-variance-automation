from food_variance.pipeline import analyze_period


def test_analyze_period_uses_canonical_variance_engine():
    result = analyze_period(1000, 850)
    assert result.variance == -150
    assert result.variance_pct == -15
