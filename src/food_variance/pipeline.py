from datetime import date

from .calculator import calculate_variance
from .models import StoreSnapshot, VarianceResult


def analyze_period(
    store_id: str,
    period: date,
    kitchen_sales: float,
    cstore_sales: float,
    gp_before: float = 0.0,
    gp_after: float = 0.0,
) -> VarianceResult:
    """Build a normalized snapshot and run the canonical variance engine."""
    snapshot = StoreSnapshot(
        store_id=store_id,
        store_name=store_id,
        period=period,
        kitchen_sales=kitchen_sales,
        cstore_sales=cstore_sales,
        gp_before=gp_before,
        gp_after=gp_after,
    )
    return calculate_variance(current=snapshot)
