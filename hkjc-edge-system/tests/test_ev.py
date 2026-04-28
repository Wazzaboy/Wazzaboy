from __future__ import annotations

from src.models.ev import edge, expected_value, uncertainty_haircut


def test_expected_value_formula() -> None:
    ev = expected_value(probability=0.4, decimal_odds=3.0)
    assert round(ev, 6) == 0.2


def test_edge_formula() -> None:
    assert round(edge(0.33, 0.30), 6) == 0.03


def test_uncertainty_haircut() -> None:
    assert round(uncertainty_haircut(0.1, 0.25), 6) == 0.075
