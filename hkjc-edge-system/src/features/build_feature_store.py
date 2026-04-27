from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.features.leakage_tags import PRE_RACE, TARGET, build_feature_tags
from src.models.market_probability import safe_odds_to_implied_probability


@dataclass(frozen=True)
class FeatureStoreBuildStats:
    rows: int
    races: int
    missing_odds_rows: int
    output_path: Path
    manifest_path: Path


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def build_feature_store(processed_dir: Path) -> FeatureStoreBuildStats:
    races_path = processed_dir / "races.csv"
    runners_path = processed_dir / "runners.csv"

    races = pd.read_csv(races_path)
    runners = pd.read_csv(runners_path)

    keep_races = [
        "race_id",
        "race_date",
        "racecourse",
        "race_no",
        "class",
        "distance",
        "going",
        "surface",
        "course",
        "source_url",
        "source_name",
        "source_page_type",
        "extraction_timestamp",
    ]
    keep_runners = [
        "runner_id",
        "race_id",
        "horse_no",
        "horse_name",
        "draw",
        "jockey",
        "trainer",
        "carried_weight",
        "handicap_rating",
        "odds",
        "finish_position",
        "source_url",
        "source_name",
        "source_page_type",
        "extraction_timestamp",
    ]

    feature_df = runners[keep_runners].merge(
        races[keep_races], on="race_id", how="left", suffixes=("_runner", "_race")
    )

    feature_df["draw_num"] = _to_numeric(feature_df["draw"])
    feature_df["carried_weight_num"] = _to_numeric(feature_df["carried_weight"])
    feature_df["handicap_rating_num"] = _to_numeric(feature_df["handicap_rating"])
    feature_df["market_odds"] = _to_numeric(feature_df["odds"])
    feature_df["market_implied_prob_raw"] = feature_df["market_odds"].map(safe_odds_to_implied_probability)
    feature_df["target_win"] = (_to_numeric(feature_df["finish_position"]) == 1).astype(int)

    feature_df["pre_race_feature_set_version"] = "v1"
    feature_df["odds_quality_note"] = (
        "Historical odds snapshots unavailable for many races; final odds are not equivalent to live bet-time odds."
    )

    ordered_cols = [
        "race_id",
        "runner_id",
        "race_date",
        "racecourse",
        "race_no",
        "horse_no",
        "horse_name",
        "draw_num",
        "carried_weight_num",
        "handicap_rating_num",
        "jockey",
        "trainer",
        "market_odds",
        "market_implied_prob_raw",
        "target_win",
        "pre_race_feature_set_version",
        "odds_quality_note",
        "source_url_runner",
        "source_name_runner",
        "source_page_type_runner",
        "extraction_timestamp_runner",
        "source_url_race",
        "source_name_race",
        "source_page_type_race",
        "extraction_timestamp_race",
    ]
    feature_df = feature_df[ordered_cols]

    output_path = processed_dir / "feature_store.csv"
    feature_df.to_csv(output_path, index=False)

    manifest_path = processed_dir / "feature_manifest.csv"
    feature_tags = build_feature_tags(feature_df.columns)
    manifest_rows = [
        {"feature_name": name, "feature_tag": feature_tags[name], "usable_for_prediction": feature_tags[name] == PRE_RACE}
        for name in feature_df.columns
    ]
    manifest_rows.append({"feature_name": "target_win", "feature_tag": TARGET, "usable_for_prediction": False})
    manifest = pd.DataFrame(manifest_rows).drop_duplicates(subset=["feature_name"], keep="first")
    manifest.to_csv(manifest_path, index=False)

    return FeatureStoreBuildStats(
        rows=int(len(feature_df)),
        races=int(feature_df["race_id"].nunique()),
        missing_odds_rows=int(feature_df["market_implied_prob_raw"].isna().sum()),
        output_path=output_path,
        manifest_path=manifest_path,
    )
