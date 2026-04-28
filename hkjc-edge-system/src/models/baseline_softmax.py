from __future__ import annotations

import math

import pandas as pd

MODEL_STATUS = "scaffold_only"
COEFFICIENT_SOURCE = "placeholder_not_fitted"
PLACEHOLDER_COEFFICIENTS = {
    "draw_num": -0.03,
    "handicap_rating_num": 0.04,
    "carried_weight_num": -0.02,
}


def softmax(scores: list[float]) -> list[float]:
    if not scores:
        return []
    max_score = max(scores)
    exps = [math.exp(score - max_score) for score in scores]
    denom = sum(exps)
    if denom == 0:
        return [0.0 for _ in scores]
    return [value / denom for value in exps]


def fundamental_score(draw_num: float, rating_num: float, carried_weight_num: float) -> float:
    """Return a scaffold-only score from placeholder coefficients.

    These coefficients are not fitted and must not be used as production betting
    model coefficients. They exist only to keep the pipeline executable while the
    verified historical dataset and fitted model are still under construction.
    """
    draw = 0.0 if pd.isna(draw_num) else float(draw_num)
    rating = 0.0 if pd.isna(rating_num) else float(rating_num)
    weight = 0.0 if pd.isna(carried_weight_num) else float(carried_weight_num)
    return (
        PLACEHOLDER_COEFFICIENTS["draw_num"] * draw
        + PLACEHOLDER_COEFFICIENTS["handicap_rating_num"] * rating
        + PLACEHOLDER_COEFFICIENTS["carried_weight_num"] * weight
    )


def add_fundamental_probabilities(df: pd.DataFrame, race_id_col: str = "race_id") -> pd.DataFrame:
    out = df.copy()
    out["fundamental_score"] = out.apply(
        lambda row: fundamental_score(row["draw_num"], row["handicap_rating_num"], row["carried_weight_num"]), axis=1
    )

    probabilities: list[float] = []
    for _, race_df in out.groupby(race_id_col, sort=False):
        probabilities.extend(softmax(race_df["fundamental_score"].tolist()))

    out["fundamental_prob"] = probabilities
    out["fundamental_model_status"] = MODEL_STATUS
    out["fundamental_coefficient_source"] = COEFFICIENT_SOURCE
    return out
