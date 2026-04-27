#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import csv
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.logging_utils import MissingDataLogEntry, append_csv_row, ensure_log_files, log_missing_data
from src.hkhorsedb.fetch import fetch_hkhorsedb_page
from src.hkhorsedb.parse_tables import parse_hkhorsedb_tables


def _write(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def main() -> int:
    logs_dir = REPO_ROOT / "logs"
    ensure_log_files(logs_dir)

    registry_path = REPO_ROOT / "data" / "processed" / "hkhorsedb" / "source_registry.csv"
    if not registry_path.exists():
        raise SystemExit("run_hkhorsedb_discovery.py first")

    with registry_path.open("r", newline="", encoding="utf-8") as handle:
        registry_rows = list(csv.DictReader(handle))

    processed_dir = REPO_ROOT / "data" / "processed" / "hkhorsedb"
    raw_root = REPO_ROOT / "data" / "raw"

    horses: list[dict[str, str]] = []
    races: list[dict[str, str]] = []
    runners: list[dict[str, str]] = []

    for row in registry_rows:
        url = row["source_url"]
        page_type = row["source_page_type"]

        fetched = fetch_hkhorsedb_page(source_url=url, source_page_type=page_type, raw_root_dir=raw_root)
        if fetched.status == "restricted":
            append_csv_row(
                logs_dir / "restricted_pages_log.csv",
                {
                    "source_name": "HKHorseDB",
                    "source_url": url,
                    "source_page_type": page_type,
                    "restriction_type": "membership_or_access",
                    "access_status": "restricted",
                    "reason": "restricted_at_fetch",
                    "next_action": "do_not_bypass",
                },
            )
            continue
        if fetched.status != "public":
            log_missing_data(
                logs_dir,
                MissingDataLogEntry(
                    source_name="HKHorseDB",
                    source_url=url,
                    source_page_type=page_type,
                    entity_type="source_page",
                    entity_key=url,
                    missing_field="page_html",
                    reason=fetched.status,
                    attempted_action="run_hkhorsedb_extraction.fetch",
                    next_action="retry",
                ),
            )
            continue

        parsed_horses, parsed_races, parsed_runners = parse_hkhorsedb_tables(
            html=fetched.html,
            source_url=url,
            source_page_type=page_type,
            extraction_timestamp=fetched.extraction_timestamp,
        )
        horses.extend(parsed_horses)
        races.extend(parsed_races)
        runners.extend(parsed_runners)

    _write(processed_dir / "horses.csv", horses, ["source_url", "source_name", "source_page_type", "extraction_timestamp", "horse_key", "horse_name", "raw_value"])
    _write(processed_dir / "races.csv", races, ["source_url", "source_name", "source_page_type", "extraction_timestamp", "race_key", "race_name", "raw_value"])
    _write(processed_dir / "runners.csv", runners, ["source_url", "source_name", "source_page_type", "extraction_timestamp", "runner_key", "runner_name", "raw_value"])

    print(f"horses_rows={len(horses)}")
    print(f"races_rows={len(races)}")
    print(f"runners_rows={len(runners)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
