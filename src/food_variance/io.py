"""Small, dependency-free serialization helpers for analysis results."""
from __future__ import annotations
import json
from dataclasses import asdict
from .models import VarianceResult


def result_to_dict(result: VarianceResult) -> dict:
    """Convert a result into JSON-safe primitive values."""
    data = asdict(result)
    data["period"] = result.period.isoformat()
    data["warnings"] = list(result.warnings)
    return data


def result_to_json(result: VarianceResult, *, indent: int = 2) -> str:
    if indent < 0:
        raise ValueError("indent must be non-negative")
    return json.dumps(result_to_dict(result), indent=indent, sort_keys=True)
