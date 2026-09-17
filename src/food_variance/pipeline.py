from .calculator import calculate_variance
from .models import VarianceResult


def analyze_period(budget: float, actual: float) -> VarianceResult:
    """Run the canonical budget-vs-actual calculation for one period."""
    return calculate_variance(budget=budget, actual=actual)
