from __future__ import annotations

from src.models.staking import fractional_kelly


def test_fractional_kelly_positive_case() -> None:
    stake = fractional_kelly(probability=0.4, decimal_odds=3.0, fraction=0.25, uncertainty=0.0)
    assert round(stake, 6) == 0.025


def test_fractional_kelly_non_positive_edge_returns_zero() -> None:
    assert fractional_kelly(probability=0.2, decimal_odds=2.0, fraction=0.25, uncertainty=0.0) == 0.0
