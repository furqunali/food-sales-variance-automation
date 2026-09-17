"""Validated runtime configuration for the analysis package."""
from __future__ import annotations
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    reconciliation_tolerance: float = 2.0
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        raw = os.getenv("RECONCILIATION_TOLERANCE", "2.0")
        try:
            tolerance = float(raw)
        except ValueError as exc:
            raise ValueError("RECONCILIATION_TOLERANCE must be numeric") from exc
        if tolerance < 0:
            raise ValueError("RECONCILIATION_TOLERANCE must be non-negative")
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL is not a valid logging level")
        return cls(reconciliation_tolerance=tolerance, log_level=level)
