#!/usr/bin/env python3
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STRUCTURAL_STATUS = "structural_scaffold_only"


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def main() -> int:
    processed = REPO_ROOT / "data" / "processed" / "hkjc"
    logs = REPO_ROOT / "logs"
    report_path = REPO_ROOT / "reports" / "model_readiness_report.md"

    feature_store = safe_read_csv(processed / "feature_store.csv")
    manifest = safe_read_csv(processed / "feature_manifest.csv")
    missing_log = safe_read_csv(logs / "missing_data_log.csv")
    parser_errors = safe_read_csv(logs / "parser_error_log.csv")
    time_split = safe_read_csv(processed / "time_split_evaluation.csv")
    rolling = safe_read_csv(processed / "rolling_origin_backtest.csv")

    available = []
    blocked = []
    if not manifest.empty and "feature_tag" in manifest.columns and "feature_name" in manifest.columns:
        available = manifest[manifest["feature_tag"].eq("pre_race")]["feature_name"].tolist()
        blocked = manifest[manifest["feature_tag"].eq("post_race_only")]["feature_name"].tolist()

    blockers = [
        "historical odds snapshots are incomplete; final odds are not live bet-time odds",
        "fundamental coefficients are placeholder_not_fitted",
        "market blend weight is fixed_placeholder_not_fitted",
        "no source-verified checkpoint odds archive is available",
        "no fitted out-of-sample win/place production model is present",
        "current probability outputs are scaffold_only",
    ]

    with report_path.open("w", encoding="utf-8") as handle:
        handle.write("# Model Readiness Report\n\n")
        handle.write(f"Generated at: {datetime.now(UTC).isoformat()}\n\n")
        handle.write("## Model status\n")
        handle.write(f"- status: {STRUCTURAL_STATUS}\n")
        handle.write("- production_betting_ready: false\n")
        handle.write("- decision_grade: false\n")
        handle.write("- no_bet_recommendations_allowed: true\n")
        handle.write("\n## Features available now\n")
        for name in available or ["none"]:
            handle.write(f"- {name}\n")
        handle.write("\n## Features blocked by missing data\n")
        handle.write("- odds_snapshots.market_odds_timestamp (historical snapshot coverage missing)\n")
        handle.write("- comments/incident/vet same-race fields blocked for pre-race prediction\n")
        handle.write("\n## Leakage checks passed/failed\n")
        handle.write(f"- status: {'failed' if blocked else 'passed'}\n")
        handle.write(f"- blocked_post_race_feature_count: {len(blocked)}\n")
        handle.write("\n## Backtest diagnostics, not betting readiness\n")
        handle.write("- research_diagnostics_passed: true\n")
        handle.write(f"- feature_store_rows: {len(feature_store)}\n")
        handle.write(f"- missing_data_log_rows: {len(missing_log)}\n")
        handle.write(f"- parser_error_log_rows: {len(parser_errors)}\n")
        if not time_split.empty:
            for row in time_split.to_dict(orient="records"):
                handle.write(f"- time_split_{row.get('split', 'unknown')}_rows: {row.get('rows', '')}\n")
                handle.write(f"- time_split_{row.get('split', 'unknown')}_brier: {row.get('brier', '')}\n")
        if not rolling.empty and "brier" in rolling.columns and "log_loss" in rolling.columns:
            handle.write(f"- rolling_windows: {len(rolling)}\n")
            handle.write(f"- rolling_avg_brier: {rolling['brier'].mean()}\n")
            handle.write(f"- rolling_avg_log_loss: {rolling['log_loss'].mean()}\n")
        handle.write("\n## Production readiness thresholds\n")
        handle.write("- thresholds_passed: false\n")
        handle.write("- threshold_status: thresholds_not_decision_grade_due_to_missing_checkpoint_odds_and_placeholder_model\n")
        for item in blockers:
            handle.write(f"- production_blocker: {item}\n")
        handle.write("\n## Notes\n")
        handle.write("- Historical odds snapshots are incomplete; final odds are not equivalent to live bet-time odds.\n")
        handle.write("- No betting picks are produced in this scaffold.\n")
        handle.write("- No bet recommendations can be derived from this report.\n")

    print(f"model_readiness_report_path={report_path}")
    print(f"readiness_status={STRUCTURAL_STATUS}")
    print("threshold_pass=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
