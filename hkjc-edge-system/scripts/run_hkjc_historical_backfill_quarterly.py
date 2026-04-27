#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import UTC, date, datetime
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.quarterly import count_missing_required_fields, dedupe_rows_by_key, iter_quarter_windows
from scripts.run_hkjc_results_extraction import RACES_COLUMNS, RUNNERS_COLUMNS, RESULTS_COLUMNS, DIVIDENDS_COLUMNS
from scripts.run_hkjc_historical_backfill import COMMENTS_COLUMNS, INCIDENT_COLUMNS, RACE_CARD_COLUMNS, CHANGES_COLUMNS

TABLES = [
    "races.csv",
    "runners.csv",
    "results.csv",
    "dividends.csv",
    "comments.csv",
    "incidents.csv",
    "race_cards.csv",
    "changes.csv",
]

TABLE_COLUMNS = {
    "races.csv": RACES_COLUMNS,
    "runners.csv": RUNNERS_COLUMNS,
    "results.csv": RESULTS_COLUMNS,
    "dividends.csv": DIVIDENDS_COLUMNS,
    "comments.csv": COMMENTS_COLUMNS,
    "incidents.csv": INCIDENT_COLUMNS,
    "race_cards.csv": RACE_CARD_COLUMNS,
    "changes.csv": CHANGES_COLUMNS,
}


def _parse_date(raw: str) -> date:
    return datetime.strptime(raw, "%Y-%m-%d").date()


def _load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    """Write rows deterministically, including header-only zero-row outputs.

    A quarterly run must describe the requested extraction window. Returning early on
    empty rows can preserve stale CSVs from previous windows and corrupt joins.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = fieldnames or (list(rows[0].keys()) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def _run_single_batch(start_date: str, end_date: str) -> None:
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_hkjc_historical_backfill.py"),
        "--start-date",
        start_date,
        "--end-date",
        end_date,
    ]
    subprocess.run(cmd, check=True)


def _append_report(report_path: Path, lines: list[str]) -> None:
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write("\n## Quarterly Historical Backfill Summary\n")
        for line in lines:
            handle.write(f"- {line}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run HKJC historical backfill quarter-by-quarter")
    parser.add_argument("--start-date", default="2020-01-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    args = parser.parse_args()

    start_date = _parse_date(args.start_date)
    end_date = _parse_date(args.end_date)

    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"
    quarterly_dir = processed_dir / "quarterly" / "backfill"

    merged_tables: dict[str, list[dict[str, str]]] = {name: [] for name in TABLES}

    windows = iter_quarter_windows(start_date, end_date)
    for idx, window in enumerate(windows, start=1):
        _run_single_batch(window.start_date.isoformat(), window.end_date.isoformat())

        for name in TABLES:
            current_rows = _load_rows(processed_dir / name)
            merged_tables[name].extend(current_rows)
            _write_rows(
                quarterly_dir / f"batch_{idx:03d}_{window.start_date}_{window.end_date}_{name}",
                current_rows,
                TABLE_COLUMNS[name],
            )

        deduped_races, dup_races = dedupe_rows_by_key(merged_tables["races.csv"], "race_id")
        deduped_runners, dup_runners = dedupe_rows_by_key(merged_tables["runners.csv"], "runner_id")
        missing_required = count_missing_required_fields(
            deduped_races + deduped_runners,
            ["source_url", "source_name", "source_page_type", "extraction_timestamp"],
        )
        print(
            "batch="
            f"{idx}/{len(windows)} start={window.start_date} end={window.end_date} "
            f"dup_race_id={dup_races} dup_runner_id={dup_runners} missing_required={missing_required}"
        )

    for name in TABLES:
        rows = merged_tables[name]
        key = "race_id" if name == "races.csv" else "runner_id" if name == "runners.csv" else ""
        if key:
            rows, _ = dedupe_rows_by_key(rows, key)
        _write_rows(processed_dir / name, rows, TABLE_COLUMNS[name])

    deduped_races, dup_races = dedupe_rows_by_key(_load_rows(processed_dir / "races.csv"), "race_id")
    deduped_runners, dup_runners = dedupe_rows_by_key(_load_rows(processed_dir / "runners.csv"), "runner_id")
    missing_required = count_missing_required_fields(
        deduped_races + deduped_runners,
        ["source_url", "source_name", "source_page_type", "extraction_timestamp"],
    )

    _append_report(
        REPO_ROOT / "reports" / "extraction_report.md",
        [
            f"generated_at: {datetime.now(UTC).isoformat()}",
            f"range: {args.start_date} to {args.end_date}",
            f"batches: {len(windows)}",
            f"duplicate_race_id_rows: {dup_races}",
            f"duplicate_runner_id_rows: {dup_runners}",
            f"missing_required_source_fields: {missing_required}",
        ],
    )

    print(f"batches={len(windows)}")
    print(f"duplicate_race_id_rows={dup_races}")
    print(f"duplicate_runner_id_rows={dup_runners}")
    print(f"missing_required_source_fields={missing_required}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
