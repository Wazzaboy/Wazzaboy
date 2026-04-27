#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.leakage_tags import POST_RACE_ONLY, build_feature_tags
from src.models.backtest import brier_score, build_rolling_origin_windows, log_loss
from src.models.baseline_softmax import add_fundamental_probabilities
from src.models.blend import add_blended_probabilities
from src.models.calibration import add_calibrated_probabilities, fit_calibration_from_historical_folds
from src.models.market_probability import add_market_probabilities


def _build_base_predictions(feature_store: pd.DataFrame) -> pd.DataFrame:
    model_df = feature_store[
        [
            "race_id",
            "runner_id",
            "race_date",
            "target_win",
            "market_odds",
            "draw_num",
            "carried_weight_num",
            "handicap_rating_num",
        ]
    ].copy()
    model_df = add_market_probabilities(model_df, odds_col="market_odds")
    model_df = add_fundamental_probabilities(model_df)
    model_df = add_blended_probabilities(model_df, market_weight=0.60)
    model_df["race_date"] = pd.to_datetime(model_df["race_date"]).dt.date.astype(str)
    return model_df


def main() -> int:
    parser = argparse.ArgumentParser(description="Run rolling-origin HKJC backtest scaffold")
    parser.add_argument("--initial-train-days", type=int, default=3)
    parser.add_argument("--step-days", type=int, default=2)
    parser.add_argument("--test-days", type=int, default=2)
    args = parser.parse_args()

    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"
    feature_store_path = processed_dir / "feature_store.csv"
    if not feature_store_path.exists():
        raise SystemExit("feature_store.csv not found; run scripts/build_feature_store.py first")

    feature_store = pd.read_csv(feature_store_path)
    tags = build_feature_tags(feature_store.columns)
    leakage_cols = [name for name, tag in tags.items() if tag == POST_RACE_ONLY]
    if leakage_cols:
        print(f"excluded_post_race_columns={leakage_cols}")

    model_df = _build_base_predictions(feature_store)
    unique_dates = sorted(model_df["race_date"].unique().tolist())
    windows = build_rolling_origin_windows(
        unique_dates,
        initial_train_size=args.initial_train_days,
        step_size=args.step_days,
        test_size=args.test_days,
    )
    if not windows:
        raise SystemExit("no rolling-origin windows generated; adjust window sizes")

    rows: list[dict[str, str | float | int]] = []
    prior_slope: float | None = None
    prior_intercept: float | None = None

    for window in windows:
        train_df = model_df[model_df["race_date"].isin(window.train_dates)].copy()
        test_df = model_df[model_df["race_date"].isin(window.test_dates)].copy()
        if train_df.empty or test_df.empty:
            continue

        slope, intercept = fit_calibration_from_historical_folds(
            train_df,
            date_col="race_date",
            prob_col="blended_prob",
            target_col="target_win",
        )
        test_df = add_calibrated_probabilities(test_df, slope=slope, intercept=intercept)

        probabilities = test_df["calibrated_prob"].astype(float).tolist()
        targets = test_df["target_win"].astype(int).tolist()

        row = {
            "window_id": window.window_id,
            "train_start": window.train_start,
            "train_end": window.train_end,
            "test_start": window.test_start,
            "test_end": window.test_end,
            "train_rows": len(train_df),
            "test_rows": len(test_df),
            "slope": slope,
            "intercept": intercept,
            "slope_drift": 0.0 if prior_slope is None else slope - prior_slope,
            "intercept_drift": 0.0 if prior_intercept is None else intercept - prior_intercept,
            "brier": brier_score(probabilities, targets),
            "log_loss": log_loss(probabilities, targets),
        }
        rows.append(row)

        prior_slope = slope
        prior_intercept = intercept

    model_run_timestamp = datetime.now(UTC).isoformat()
    for row in rows:
        row["model_run_timestamp"] = model_run_timestamp

    out = pd.DataFrame(rows)
    cols = ["model_run_timestamp"] + [c for c in out.columns if c != "model_run_timestamp"]
    output_path = processed_dir / "rolling_origin_backtest.csv"
    out[cols].to_csv(output_path, index=False)

    print(f"rolling_origin_backtest_path={output_path}")
    print(f"windows={len(out)}")
    if not out.empty:
        print(f"avg_brier={out['brier'].mean()}")
        print(f"avg_log_loss={out['log_loss'].mean()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
