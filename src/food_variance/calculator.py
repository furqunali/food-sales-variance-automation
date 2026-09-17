"""Deterministic calculations for monthly sales and margin variance."""
from __future__ import annotations
from .models import StoreSnapshot, VarianceResult


def calculate_margin(snapshot: StoreSnapshot) -> float:
    """Return gross-profit percentage change as a decimal fraction."""
    return snapshot.gp_after - snapshot.gp_before


def calculate_variance(
    current: StoreSnapshot,
    baseline: StoreSnapshot | None = None,
    *,
    tolerance: float = 2.0,
) -> VarianceResult:
    """Compare a snapshot with an optional baseline and reconcile product mix.

    ``tolerance`` is expressed in the same currency units as sales. Negative
    tolerances are rejected so callers cannot accidentally disable validation.
    """
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")

    baseline_sales = baseline.total_sales() if baseline else 0.0
    sales_variance = current.total_sales() - baseline_sales if baseline else current.total_sales()
    margin_variance = calculate_margin(current) - (calculate_margin(baseline) if baseline else 0.0)
    mix_variance = current.mix_total() - current.kitchen_sales

    warnings: list[str] = []
    if abs(mix_variance) > tolerance:
        warnings.append("product mix does not reconcile with kitchen sales")
    if current.kitchen_sales < 0 or current.cstore_sales < 0:
        warnings.append("sales values contain a negative amount")
    if current.override_count < 0:
        warnings.append("override count cannot be negative")

    return VarianceResult(
        store_id=current.store_id,
        period=current.period,
        sales_variance=sales_variance,
        margin_variance=margin_variance,
        mix_variance=mix_variance,
        reconciliation_ok=not warnings,
        warnings=tuple(warnings),
    )
