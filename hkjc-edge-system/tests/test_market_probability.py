from __future__ import annotations

import pandas as pd

from src.models.market_probability import add_market_probabilities, normalize_overround, safe_odds_to_implied_probability


def test_safe_odds_to_implied_probability() -> None:
    assert safe_odds_to_implied_probability(2.0) == 0.5
    assert safe_odds_to_implied_probability(0.9) is None


def test_normalize_overround_sums_to_one() -> None:
    probs = normalize_overround([0.5, 0.25, 0.25])
    assert round(sum(probs), 8) == 1.0


def test_add_market_probabilities_normalizes_by_race() -> None:
    df = pd.DataFrame(
        [
            {"race_id": "R1", "market_odds": 2.0},
            {"race_id": "R1", "market_odds": 4.0},
            {"race_id": "R2", "market_odds": 3.0},
            {"race_id": "R2", "market_odds": 3.0},
        ]
    )
    out = add_market_probabilities(df)
    assert round(float(out[out["race_id"] == "R1"]["market_prob"].sum()), 8) == 1.0
    assert round(float(out[out["race_id"] == "R2"]["market_prob"].sum()), 8) == 1.0
