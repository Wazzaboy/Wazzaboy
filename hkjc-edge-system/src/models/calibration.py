from __future__ import annotations

import math

import pandas as pd


EPSILON = 1e-6


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def _clip_probability(probability: float) -> float:
    return min(max(float(probability), EPSILON), 1 - EPSILON)


def calibrate_probability(probability: float, slope: float = 1.0, intercept: float = 0.0) -> float:
    p = _clip_probability(probability)
    logit = math.log(p / (1 - p))
    return _sigmoid((slope * logit) + intercept)


def fit_logistic_calibration(
    probabilities: list[float],
    targets: list[int],
    *,
    epochs: int = 250,
    learning_rate: float = 0.05,
) -> tuple[float, float]:
    if len(probabilities) != len(targets):
        raise ValueError("probabilities and targets length mismatch")
    if not probabilities:
        return 1.0, 0.0

    x_vals = [math.log(_clip_probability(p) / (1 - _clip_probability(p))) for p in probabilities]
    y_vals = [float(v) for v in targets]

    slope = 1.0
    intercept = 0.0
    n = float(len(x_vals))

    for _ in range(epochs):
        grad_slope = 0.0
        grad_intercept = 0.0
        for x, y in zip(x_vals, y_vals, strict=True):
            pred = _sigmoid((slope * x) + intercept)
            diff = pred - y
            grad_slope += diff * x
            grad_intercept += diff

        slope -= learning_rate * (grad_slope / n)
        intercept -= learning_rate * (grad_intercept / n)

    return slope, intercept


def fit_calibration_from_historical_folds(
    df: pd.DataFrame,
    *,
    date_col: str = "race_date",
    prob_col: str = "blended_prob",
    target_col: str = "target_win",
    min_train_dates: int = 5,
) -> tuple[float, float]:
    working = df[[date_col, prob_col, target_col]].copy()
    working = working.dropna(subset=[date_col, prob_col, target_col])
    working[date_col] = pd.to_datetime(working[date_col])

    unique_dates = sorted(working[date_col].dt.date.unique())
    if len(unique_dates) < (min_train_dates + 1):
        return fit_logistic_calibration(
            working[prob_col].astype(float).tolist(),
            working[target_col].astype(int).tolist(),
        )

    fold_params: list[tuple[float, float]] = []
    for idx in range(min_train_dates, len(unique_dates)):
        train_dates = unique_dates[:idx]
        validation_date = unique_dates[idx]

        train_df = working[working[date_col].dt.date.isin(train_dates)]
        val_df = working[working[date_col].dt.date == validation_date]
        if train_df.empty or val_df.empty:
            continue

        slope, intercept = fit_logistic_calibration(
            train_df[prob_col].astype(float).tolist(),
            train_df[target_col].astype(int).tolist(),
        )
        fold_params.append((slope, intercept))

    if not fold_params:
        return 1.0, 0.0

    avg_slope = sum(slope for slope, _ in fold_params) / len(fold_params)
    avg_intercept = sum(intercept for _, intercept in fold_params) / len(fold_params)
    return avg_slope, avg_intercept


def add_calibrated_probabilities(df: pd.DataFrame, slope: float = 1.0, intercept: float = 0.0) -> pd.DataFrame:
    out = df.copy()
    out["calibrated_prob"] = out["blended_prob"].map(lambda p: calibrate_probability(p, slope=slope, intercept=intercept))
    return out
