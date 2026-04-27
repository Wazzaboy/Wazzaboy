from __future__ import annotations

import math

import pandas as pd


def safe_odds_to_implied_probability(decimal_odds: object) -> float | None:
    try:
        odds = float(decimal_odds)
    except (TypeError, ValueError):
        return None
    if odds <= 1.0:
        return None
    return 1.0 / odds


def normalize_overround(implied_probabilities: list[float]) -> list[float]:
    total = sum(implied_probabilities)
    if total <= 0:
        return [0.0 for _ in implied_probabilities]
    return [p / total for p in implied_probabilities]


def add_market_probabilities(df: pd.DataFrame, *, race_id_col: str = "race_id", odds_col: str = "market_odds") -> pd.DataFrame:
    out = df.copy()
    out["market_implied_prob"] = out[odds_col].map(safe_odds_to_implied_probability)

    normalized: list[float] = []
    for _, race_df in out.groupby(race_id_col, sort=False):
        raw = race_df["market_implied_prob"].fillna(0.0).astype(float).tolist()
        normalized.extend(normalize_overround(raw))

    out["market_prob"] = normalized
    out["market_log_prob"] = out["market_prob"].map(lambda x: math.log(x) if x > 0 else float("-inf"))
    return out
