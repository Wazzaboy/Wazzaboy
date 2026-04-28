from __future__ import annotations


def expected_value(probability: float, decimal_odds: float) -> float:
    p = float(probability)
    odds = float(decimal_odds)
    return (p * (odds - 1.0)) - (1.0 - p)


def edge(model_probability: float, market_probability: float) -> float:
    return float(model_probability) - float(market_probability)


def uncertainty_haircut(value: float, uncertainty: float) -> float:
    haircut = min(max(float(uncertainty), 0.0), 1.0)
    return float(value) * (1.0 - haircut)
