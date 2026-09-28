"""Stable serialization boundary for variance results."""
from __future__ import annotations

from dataclasses import asdict

from .models import VarianceResult


def result_to_dict(result: VarianceResult) -> dict[str, object]:
    """Return a JSON-ready representation with stable field names."""
    data = asdict(result)
    data["period"] = result.period.isoformat()
    data["warnings"] = list(result.warnings)
    return data
