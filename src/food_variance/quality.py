"""Quality gates for variance results.

These checks keep downstream reporting deterministic and safe to publish.
"""
from __future__ import annotations

from .models import VarianceResult


def quality_gate(result: VarianceResult) -> None:
    """Raise when a variance result is not safe for downstream reporting."""
    if not result.store_id.strip():
        raise ValueError("store_id must be non-empty")
    if result.reconciliation_ok is False and not result.warnings:
        raise ValueError("failed reconciliation must include warnings")
    if any(not warning.strip() for warning in result.warnings):
        raise ValueError("warnings must contain non-empty messages")
