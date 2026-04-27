#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.leakage_tags import POST_RACE_ONLY, build_feature_tags
from src.models.baseline_softmax import add_fundamental_probabilities
from src.models.blend import add_blended_probabilities
from src.models.calibration import add_calibrated_probabilities, fit_calibration_from_historical_folds
from src.models.market_probability import add_market_probabilities


def _split_by_date(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    working = df.copy()
    working["race_date"] = pd.to_datetime(working["race_date"])

    unique_dates = sorted(working["race_date"].dt.date.unique())
    if len(unique_dates) < 5:
        raise ValueError("insufficient unique race dates for train/validation/test split")

    train_end_idx = max(int(len(unique_dates) * 0.6), 1)
    val_end_idx = max(int(len(unique_dates) * 0.8), train_end_idx + 1)

    train_dates = set(unique_dates[:train_end_idx])
    val_dates = set(unique_dates[train_end_idx:val_end_idx])
    test_dates = set(unique_dates[val_end_idx:])

    train_df = working[working["race_date"].dt.date.isin(train_dates)].copy()
    val_df = working[working["race_date"].dt.date.isin(val_dates)].copy()
    test_df = working[working["race_date"].dt.date.isin(test_dates)].copy()
    return train_df, val_df, test_df


def _brier_score(df: pd.DataFrame) -> float:
    if df.empty:
        return float("nan")
    return float(((df["calibrated_prob"] - df["target_win"]) ** 2).mean())


def _build_base_predictions(df: pd.DataFrame) -> pd.DataFrame:
    model_df = df[["race_id", "runner_id", "race_date", "target_win", "market_odds", "draw_num", "carried_weight_num", "handicap_rating_num"]].copy()
    model_df = add_market_probabilities(model_df, odds_col="market_odds")
    model_df = add_fundamental_probabilities(model_df)
    model_df = add_blended_probabilities(model_df, market_weight=0.60)
    return model_df


def main() -> int:
    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"
    feature_store_path = processed_dir / "feature_store.csv"
    if not feature_store_path.exists():
        raise SystemExit("feature_store.csv not found; run scripts/build_feature_store.py first")

    feature_store = pd.read_csv(feature_store_path)

    tags = build_feature_tags(feature_store.columns)
    leakage_cols = [name for name, tag in tags.items() if tag == POST_RACE_ONLY]
    if leakage_cols:
        print(f"excluded_post_race_columns={leakage_cols}")

    all_predictions = _build_base_predictions(feature_store)
    train_df, val_df, test_df = _split_by_date(all_predictions)

    slope, intercept = fit_calibration_from_historical_folds(
        train_df,
        date_col="race_date",
        prob_col="blended_prob",
        target_col="target_win",
    )

    train_df = add_calibrated_probabilities(train_df, slope=slope, intercept=intercept)
    val_df = add_calibrated_probabilities(val_df, slope=slope, intercept=intercept)
    test_df = add_calibrated_probabilities(test_df, slope=slope, intercept=intercept)

    summary = pd.DataFrame(
        [
            {"split": "train", "rows": len(train_df), "brier": _brier_score(train_df), "slope": slope, "intercept": intercept},
            {"split": "validation", "rows": len(val_df), "brier": _brier_score(val_df), "slope": slope, "intercept": intercept},
            {"split": "test", "rows": len(test_df), "brier": _brier_score(test_df), "slope": slope, "intercept": intercept},
        ]
    )
    output_path = processed_dir / "time_split_evaluation.csv"
    summary.to_csv(output_path, index=False)

    print(f"time_split_evaluation_path={output_path}")
    print(f"calibration_slope={slope:.6f}")
    print(f"calibration_intercept={intercept:.6f}")
    for row in summary.to_dict(orient="records"):
        print(f"split={row['split']} rows={row['rows']} brier={row['brier']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
