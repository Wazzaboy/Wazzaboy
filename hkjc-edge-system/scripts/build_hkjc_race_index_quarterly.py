#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.logging_utils import ensure_log_files
from src.common.quarterly import dedupe_rows_by_key, iter_quarter_windows
from src.hkjc.race_index import RACE_INDEX_COLUMNS, build_race_index


def _parse_date(raw: str) -> date:
    return datetime.strptime(raw, "%Y-%m-%d").date()


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    """Write rows deterministically, including header-only files for zero-row batches.

    This intentionally overwrites existing output even when no rows are present. A zero-row
    extraction window must never leave stale rows from a prior run on disk.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = fieldnames or (list(rows[0].keys()) if rows else RACE_INDEX_COLUMNS)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HKJC race index in quarter batches")
    parser.add_argument("--start-date", default="2020-01-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    args = parser.parse_args()

    start_date = _parse_date(args.start_date)
    end_date = _parse_date(args.end_date)

    logs_dir = REPO_ROOT / "logs"
    ensure_log_files(logs_dir)

    quarterly_dir = REPO_ROOT / "data" / "processed" / "hkjc" / "quarterly" / "race_index"
    output_path = REPO_ROOT / "data" / "processed" / "hkjc" / "race_index.csv"
    raw_root_dir = REPO_ROOT / "data" / "raw"

    all_rows: list[dict[str, str]] = []
    windows = iter_quarter_windows(start_date, end_date)
    for idx, window in enumerate(windows, start=1):
        batch_output = quarterly_dir / f"race_index_batch_{idx:03d}_{window.start_date}_{window.end_date}.csv"
        stats = build_race_index(
            start_date=window.start_date,
            end_date=window.end_date,
            output_path=batch_output,
            raw_root_dir=raw_root_dir,
            logs_dir=logs_dir,
        )
        batch_rows = _load_csv_rows(batch_output)
        all_rows.extend(batch_rows)
        print(f"batch={idx}/{len(windows)} start={window.start_date} end={window.end_date} rows={stats.rows}")

    deduped, duplicate_count = dedupe_rows_by_key(all_rows, "race_id")
    deduped.sort(key=lambda row: (row.get("race_date", ""), row.get("racecourse", ""), row.get("race_no", "")))
    _write_rows(output_path, deduped, RACE_INDEX_COLUMNS)

    print(f"output_path={output_path}")
    print(f"batches={len(windows)}")
    print(f"total_rows_before_dedupe={len(all_rows)}")
    print(f"duplicate_race_id_rows={duplicate_count}")
    print(f"rows_after_dedupe={len(deduped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
