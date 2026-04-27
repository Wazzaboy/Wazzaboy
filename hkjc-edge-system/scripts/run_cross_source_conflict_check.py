#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import csv
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.logging_utils import append_csv_row, ensure_log_files


def run_conflict_check(root: Path) -> int:
    hkjc_runners = root / "data" / "processed" / "hkjc" / "runners.csv"
    hkh_runners = root / "data" / "processed" / "hkhorsedb" / "runners.csv"
    logs_dir = root / "logs"
    ensure_log_files(logs_dir)

    if not hkjc_runners.exists() or not hkh_runners.exists():
        return 0

    with hkjc_runners.open("r", newline="", encoding="utf-8") as handle:
        hkjc_rows = list(csv.DictReader(handle))
    with hkh_runners.open("r", newline="", encoding="utf-8") as handle:
        hkh_rows = list(csv.DictReader(handle))

    hkjc_names = {row.get("horse_name", "").strip().lower(): row for row in hkjc_rows if row.get("horse_name")}

    conflicts = 0
    for row in hkh_rows:
        hkh_name = row.get("runner_name", "").strip().lower()
        if not hkh_name:
            continue
        if hkh_name in hkjc_names:
            continue
        append_csv_row(
            logs_dir / "conflict_log.csv",
            {
                "entity_type": "runner",
                "entity_key": row.get("runner_key", ""),
                "field_name": "horse_name",
                "hkjc_value": "not_found",
                "hkjc_source_url": "",
                "secondary_source_name": "HKHorseDB",
                "secondary_value": row.get("runner_name", ""),
                "secondary_source_url": row.get("source_url", ""),
                "severity": "low",
                "recommended_resolution": "manual_review",
            },
        )
        conflicts += 1

    return conflicts


def main() -> int:
    conflicts = run_conflict_check(REPO_ROOT)
    print(f"conflicts_logged={conflicts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
