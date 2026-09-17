"""Typed domain models used by the variance pipeline."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Mapping


@dataclass(frozen=True)
class StoreSnapshot:
    """Normalized monthly observations for one store."""
    store_id: str
    store_name: str
    period: date
    kitchen_sales: float = 0.0
    cstore_sales: float = 0.0
    gp_before: float = 0.0
    gp_after: float = 0.0
    discount_amount: float = 0.0
    override_count: int = 0
    product_mix: Mapping[str, float] = field(default_factory=dict)

    def total_sales(self) -> float:
        return self.kitchen_sales + self.cstore_sales

    def mix_total(self) -> float:
        return sum(float(v) for v in self.product_mix.values())


@dataclass(frozen=True)
class VarianceResult:
    """Calculated variance and reconciliation metrics."""
    store_id: str
    period: date
    sales_variance: float
    margin_variance: float
    mix_variance: float
    reconciliation_ok: bool
    warnings: tuple[str, ...] = ()

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)
