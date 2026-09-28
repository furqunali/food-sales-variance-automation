from datetime import date

import pytest

from food_variance.models import VarianceResult
from food_variance.quality import quality_gate


def test_quality_gate_accepts_reconciled_result():
    result = VarianceResult("S1", date(2026, 9, 1), 10.0, 1.0, 0.0, True)
    quality_gate(result)


def test_quality_gate_requires_warning_for_failed_reconciliation():
    result = VarianceResult("S1", date(2026, 9, 1), 10.0, 1.0, 5.0, False, ())
    with pytest.raises(ValueError, match="failed reconciliation"):
        quality_gate(result)


def test_quality_gate_rejects_blank_warning():
    result = VarianceResult("S1", date(2026, 9, 1), 10.0, 1.0, 0.0, True, (" ",))
    with pytest.raises(ValueError, match="warnings"):
        quality_gate(result)
