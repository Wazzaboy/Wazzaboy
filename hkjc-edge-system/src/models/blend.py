from __future__ import annotations

import pandas as pd


def market_blend(fundamental_prob: float, market_prob: float, market_weight: float = 0.6) -> float:
    weight = min(max(market_weight, 0.0), 1.0)
    return ((1 - weight) * float(fundamental_prob)) + (weight * float(market_prob))


def add_blended_probabilities(df: pd.DataFrame, market_weight: float = 0.6) -> pd.DataFrame:
    out = df.copy()
    out["blended_prob"] = out.apply(
        lambda row: market_blend(row["fundamental_prob"], row["market_prob"], market_weight=market_weight), axis=1
    )
    return out
