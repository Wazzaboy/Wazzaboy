#!/usr/bin/env python3
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

MIN_SPLIT_ROWS = 200
MAX_BRIER = 0.080
MAX_LOG_LOSS = 0.260
MIN_ROLLING_WINDOWS = 3


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _evaluate_thresholds(time_split_eval: pd.DataFrame, rolling_eval: pd.DataFrame) -> tuple[bool, list[str]]:
    failures: list[str] = []

    if time_split_eval.empty:
        failures.append("missing time_split_evaluation.csv")
    else:
        for _, row in time_split_eval.iterrows():
            split = str(row.get("split", "unknown"))
            rows = int(row.get("rows", 0))
            brier = float(row.get("brier", 1.0))
            if rows < MIN_SPLIT_ROWS:
                failures.append(f"{split} rows {rows} < {MIN_SPLIT_ROWS}")
            if brier > MAX_BRIER:
                failures.append(f"{split} brier {brier:.4f} > {MAX_BRIER:.4f}")

    if rolling_eval.empty:
        failures.append("missing rolling_origin_backtest.csv")
    else:
        if len(rolling_eval) < MIN_ROLLING_WINDOWS:
            failures.append(f"rolling windows {len(rolling_eval)} < {MIN_ROLLING_WINDOWS}")
        if int(rolling_eval["test_rows"].min()) < MIN_SPLIT_ROWS:
            failures.append(
                f"rolling test_rows min {int(rolling_eval['test_rows'].min())} < {MIN_SPLIT_ROWS}"
            )
        if float(rolling_eval["brier"].max()) > MAX_BRIER:
            failures.append(
                f"rolling max brier {float(rolling_eval['brier'].max()):.4f} > {MAX_BRIER:.4f}"
            )
        if float(rolling_eval["log_loss"].max()) > MAX_LOG_LOSS:
            failures.append(
                f"rolling max log_loss {float(rolling_eval['log_loss'].max()):.4f} > {MAX_LOG_LOSS:.4f}"
            )

    return len(failures) == 0, failures


def main() -> int:
    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"
    logs_dir = REPO_ROOT / "logs"
    report_path = REPO_ROOT / "reports" / "model_readiness_report.md"

    feature_store = _safe_read_csv(processed_dir / "feature_store.csv")
    manifest = _safe_read_csv(processed_dir / "feature_manifest.csv")
    missing_log = _safe_read_csv(logs_dir / "missing_data_log.csv")
    parser_errors = _safe_read_csv(logs_dir / "parser_error_log.csv")
    time_split_eval = _safe_read_csv(processed_dir / "time_split_evaluation.csv")
    rolling_eval = _safe_read_csv(processed_dir / "rolling_origin_backtest.csv")

    available_features = manifest[manifest.get("feature_tag", "") == "pre_race"]["feature_name"].tolist() if not manifest.empty else []
    blocked_features = manifest[manifest.get("feature_tag", "") == "post_race_only"]["feature_name"].tolist() if not manifest.empty else []

    leakage_failures = len(blocked_features)
    leakage_status = "failed" if leakage_failures else "passed"

    threshold_pass, threshold_failures = _evaluate_thresholds(time_split_eval, rolling_eval)
    readiness_status = "provisionally_ready" if threshold_pass else "not_ready"

    notes = [
        "Historical odds snapshots are incomplete; final odds are not equivalent to live bet-time odds.",
        "No betting picks are produced in this scaffold.",
    ]

    with report_path.open("w", encoding="utf-8") as handle:
        handle.write("# Model Readiness Report\n\n")
        handle.write(f"Generated at: {datetime.now(UTC).isoformat()}\n\n")

        handle.write("## Features available now\n")
        for name in available_features:
            handle.write(f"- {name}\n")
        if not available_features:
            handle.write("- none\n")

        handle.write("\n## Features blocked by missing data\n")
        handle.write("- odds_snapshots.market_odds_timestamp (historical snapshot coverage missing)\n")
        handle.write("- comments/incident/vet same-race fields blocked for pre-race prediction\n")

        handle.write("\n## Leakage checks passed/failed\n")
        handle.write(f"- status: {leakage_status}\n")
        handle.write(f"- blocked_post_race_feature_count: {leakage_failures}\n")

        handle.write("\n## Backtest readiness\n")
        handle.write(f"- status: {readiness_status}\n")
        handle.write(f"- feature_store_rows: {len(feature_store)}\n")
        handle.write(f"- missing_data_log_rows: {max(len(missing_log), 0)}\n")
        handle.write(f"- parser_error_log_rows: {max(len(parser_errors), 0)}\n")
        if not time_split_eval.empty:
            for row in time_split_eval.to_dict(orient="records"):
                handle.write(f"- time_split_{row['split']}_rows: {row['rows']}\n")
                handle.write(f"- time_split_{row['split']}_brier: {row['brier']}\n")
        if not rolling_eval.empty:
            handle.write(f"- rolling_windows: {len(rolling_eval)}\n")
            handle.write(f"- rolling_avg_brier: {rolling_eval['brier'].mean()}\n")
            handle.write(f"- rolling_avg_log_loss: {rolling_eval['log_loss'].mean()}\n")

        handle.write("\n## Readiness thresholds\n")
        handle.write(f"- min_split_rows: {MIN_SPLIT_ROWS}\n")
        handle.write(f"- max_brier: {MAX_BRIER}\n")
        handle.write(f"- max_log_loss: {MAX_LOG_LOSS}\n")
        handle.write(f"- min_rolling_windows: {MIN_ROLLING_WINDOWS}\n")
        handle.write(f"- thresholds_passed: {str(threshold_pass).lower()}\n")
        if threshold_failures:
            for item in threshold_failures:
                handle.write(f"- threshold_failure: {item}\n")

        handle.write("\n## Minimum dataset requirements before serious modeling\n")
        handle.write("- At least 2 full seasons of race-level coverage with stable schema.\n")
        handle.write("- Reliable historical odds snapshot timestamps (pre-jump/near-jump).\n")
        handle.write("- Complete pre-race horse, trainer, jockey history windows for recency features.\n")
        handle.write("- Leakage audit pass across all candidate features.\n")
        handle.write("- Explicit train/validation/test date split with no race-day cross-contamination.\n")

        handle.write("\n## Notes\n")
        for note in notes:
            handle.write(f"- {note}\n")

    print(f"model_readiness_report_path={report_path}")
    print(f"readiness_status={readiness_status}")
    print(f"threshold_pass={threshold_pass}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
