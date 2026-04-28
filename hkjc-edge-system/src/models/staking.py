from __future__ import annotations

from src.models.ev import uncertainty_haircut


def fractional_kelly(probability: float, decimal_odds: float, fraction: float = 0.25, uncertainty: float = 0.0) -> float:
    p = float(probability)
    odds = float(decimal_odds)
    b = odds - 1.0
    if b <= 0:
        return 0.0

    full_kelly = ((b * p) - (1.0 - p)) / b
    full_kelly = max(0.0, full_kelly)
    adjusted = uncertainty_haircut(full_kelly, uncertainty)
    return adjusted * min(max(float(fraction), 0.0), 1.0)
