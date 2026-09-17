"""Reconciliation helpers with explicit, auditable outcomes."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    expected: float
    actual: float
    tolerance: float

    @property
    def passed(self) -> bool:
        return abs(self.expected - self.actual) <= self.tolerance


def check_amount(name: str, expected: float, actual: float, tolerance: float = 2.0) -> CheckResult:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    return CheckResult(name, float(expected), float(actual), float(tolerance))


def summarize(checks: list[CheckResult]) -> dict[str, int | bool]:
    passed = sum(check.passed for check in checks)
    failed = len(checks) - passed
    return {"passed": passed, "failed": failed, "ok": failed == 0}
