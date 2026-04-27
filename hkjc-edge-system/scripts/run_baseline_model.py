#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.leakage_tags import PRE_RACE, TARGET, build_feature_tags
from src.models.baseline_softmax import add_fundamental_probabilities
from src.models.blend import add_blended_probabilities
from src.models.calibration import add_calibrated_probabilities, fit_calibration_from_historical_folds
from src.models.ev import edge, expected_value, uncertainty_haircut
from src.models.market_probability import add_market_probabilities
from src.models.staking import fractional_kelly


def _validate_source_fields(df: pd.DataFrame) -> None:
    required_cols = [
        "source_url_runner",
        "source_name_runner",
        "source_page_type_runner",
        "extraction_timestamp_runner",
        "source_url_race",
        "source_name_race",
        "source_page_type_race",
        "extraction_timestamp_race",
    ]
    missing_cols = [name for name in required_cols if name not in df.columns]
    if missing_cols:
        raise ValueError(f"missing required source columns: {missing_cols}")

    for name in required_cols:
        if df[name].astype(str).str.strip().isin({"", "NULL"}).any():
            raise ValueError(f"invalid source provenance values found in column: {name}")


def main() -> int:
    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"
    feature_store_path = processed_dir / "feature_store.csv"
    if not feature_store_path.exists():
        raise SystemExit("feature_store.csv not found; run scripts/build_feature_store.py first")

    df = pd.read_csv(feature_store_path)
    _validate_source_fields(df)

    tags = build_feature_tags(df.columns)
    model_feature_columns = [
        name
        for name, tag in tags.items()
        if tag == PRE_RACE and name in {"draw_num", "carried_weight_num", "handicap_rating_num"}
    ]
    forbidden_columns = [name for name, tag in tags.items() if tag not in {PRE_RACE, TARGET}]
    if forbidden_columns:
        print(f"excluded_post_race_columns={forbidden_columns}")

    model_df = df[["race_id", "runner_id", "race_date", "horse_name", "target_win", "market_odds", *model_feature_columns]].copy()

    model_df = add_market_probabilities(model_df, odds_col="market_odds")
    model_df = add_fundamental_probabilities(model_df)
    model_df = add_blended_probabilities(model_df, market_weight=0.60)

    slope, intercept = fit_calibration_from_historical_folds(
        model_df,
        date_col="race_date",
        prob_col="blended_prob",
        target_col="target_win",
    )
    model_df = add_calibrated_probabilities(model_df, slope=slope, intercept=intercept)

    model_df["edge"] = model_df.apply(lambda row: edge(row["calibrated_prob"], row["market_prob"]), axis=1)
    model_df["edge_haircut"] = model_df["edge"].map(lambda value: uncertainty_haircut(value, uncertainty=0.30))
    model_df["expected_value"] = model_df.apply(lambda row: expected_value(row["calibrated_prob"], row["market_odds"]), axis=1)
    model_df["expected_value_haircut"] = model_df["expected_value"].map(lambda value: uncertainty_haircut(value, uncertainty=0.30))
    model_df["fractional_kelly_25"] = model_df.apply(
        lambda row: fractional_kelly(row["calibrated_prob"], row["market_odds"], fraction=0.25, uncertainty=0.30), axis=1
    )

    probabilities_path = processed_dir / "model_probabilities.csv"
    model_df.to_csv(probabilities_path, index=False)

    simulation_cols = ["race_id", "runner_id", "race_date", "horse_name", "expected_value_haircut", "fractional_kelly_25"]
    simulation_path = processed_dir / "betting_ev_simulation.csv"
    model_df[simulation_cols].to_csv(simulation_path, index=False)

    print(f"calibration_slope={slope:.6f}")
    print(f"calibration_intercept={intercept:.6f}")
    print(f"model_probabilities_path={probabilities_path}")
    print(f"betting_ev_simulation_path={simulation_path}")
    print(f"rows={len(model_df)}")
    print("note=no betting picks were generated; outputs are scaffolding only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
