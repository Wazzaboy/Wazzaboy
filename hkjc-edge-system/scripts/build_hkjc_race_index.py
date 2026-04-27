#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
from pathlib import Path
import csv
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.logging_utils import ensure_log_files
from src.hkjc.race_index import build_race_index


def _parse_date(raw: str) -> date:
    return datetime.strptime(raw, "%Y-%m-%d").date()


def _coverage_by_racecourse(csv_path: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            counts[row.get("racecourse", "NULL")] += 1
    return dict(sorted(counts.items()))


def _missing_field_count(csv_path: Path) -> int:
    missing = 0
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for value in row.values():
                if value == "NULL":
                    missing += 1
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Build cautious HKJC race index")
    parser.add_argument("--start-date", default="2020-01-01", help="Inclusive YYYY-MM-DD")
    parser.add_argument("--end-date", default=date.today().isoformat(), help="Inclusive YYYY-MM-DD")
    args = parser.parse_args()

    start_date = _parse_date(args.start_date)
    end_date = _parse_date(args.end_date)

    logs_dir = REPO_ROOT / "logs"
    output_path = REPO_ROOT / "data" / "processed" / "hkjc" / "race_index.csv"
    raw_root_dir = REPO_ROOT / "data" / "raw"
    ensure_log_files(logs_dir)

    stats = build_race_index(
        start_date=start_date,
        end_date=end_date,
        output_path=output_path,
        raw_root_dir=raw_root_dir,
        logs_dir=logs_dir,
    )

    coverage = _coverage_by_racecourse(output_path)
    missing_fields = _missing_field_count(output_path)

    print(f"output_path={output_path}")
    print(f"rows={stats.rows}")
    print(f"skipped_dates={stats.skipped_dates}")
    print(f"missing_fields={missing_fields}")
    print(f"coverage_by_racecourse={coverage}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
