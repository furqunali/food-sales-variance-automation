"""Production-grade food sales variance analysis package."""

from .models import StoreSnapshot, VarianceResult
from .calculator import calculate_variance, calculate_margin

__all__ = ["StoreSnapshot", "VarianceResult", "calculate_variance", "calculate_margin"]
__version__ = "1.0.0"
