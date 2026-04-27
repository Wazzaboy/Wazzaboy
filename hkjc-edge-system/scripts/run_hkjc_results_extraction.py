#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.logging_utils import MissingDataLogEntry, append_csv_row, ensure_log_files, log_missing_data
from src.hkjc.fetch import HKJC_RESULTS_BASE_URL, discover_results_urls, fetch_results_page
from src.hkjc.parse_dividends import parse_dividends_page
from src.hkjc.parse_results import ParserLayoutError, parse_results_page


RACES_COLUMNS = [
    "source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id", "meeting_id", "race_date",
    "racecourse", "race_no", "race_name", "class", "rating_band", "distance", "surface", "course", "going",
    "prize_money", "field_size", "raw_class_distance", "raw_race_header",
]
RUNNERS_COLUMNS = [
    "source_url", "source_name", "source_page_type", "extraction_timestamp", "runner_id", "race_id", "race_date",
    "racecourse", "race_no", "horse_no", "horse_name", "horse_id_or_brand_no", "draw", "jockey", "trainer",
    "carried_weight", "handicap_rating", "rating_change", "declared_body_weight", "body_weight_change", "gear",
    "gear_change", "odds", "finish_position", "beaten_margin", "race_time", "sectional_time", "running_position",
    "comments_or_notes", "raw_horse", "raw_finish_time", "raw_running_position",
]
RESULTS_COLUMNS = [
    "source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id", "runner_id", "horse_no",
    "horse_name", "finish_position", "beaten_margin", "finish_time", "running_position", "win_odds", "raw_value",
]
DIVIDENDS_COLUMNS = [
    "source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id", "pool_type",
    "winning_combination", "dividend", "raw_value",
]


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def _validate_rows(rows: list[dict[str, str]], required_columns: list[str]) -> list[str]:
    errors: list[str] = []
    for idx, row in enumerate(rows):
        for col in required_columns:
            if not str(row.get(col, "")).strip():
                errors.append(f"row {idx}: missing {col}")
    return errors


def _safe_numeric(value: str) -> bool:
    if not value or value in {"-", "N"}:
        return True
    cleaned = value.replace(",", "")
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _validate_outputs(races: list[dict[str, str]], runners: list[dict[str, str]], results: list[dict[str, str]], dividends: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_rows(races, ["source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id", "race_date"]))
    errors.extend(_validate_rows(runners, ["source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id", "runner_id"]))
    errors.extend(_validate_rows(results, ["source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id", "runner_id"]))
    errors.extend(_validate_rows(dividends, ["source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id"]))

    race_ids = [row["race_id"] for row in races if row.get("race_id")]
    if len(race_ids) != len(set(race_ids)):
        errors.append("duplicate race_id in races.csv")

    runner_ids = [row["runner_id"] for row in runners if row.get("runner_id")]
    if len(runner_ids) != len(set(runner_ids)):
        errors.append("duplicate runner_id in runners.csv")

    for row in races:
        if row.get("race_date"):
            try:
                datetime.strptime(row["race_date"], "%Y-%m-%d")
            except ValueError:
                errors.append(f"invalid race_date: {row['race_date']}")

    for row in runners:
        for col in ["carried_weight", "declared_body_weight", "draw", "odds"]:
            if not _safe_numeric(row.get(col, "")):
                errors.append(f"unsafe numeric parse in {col}: {row.get(col, '')}")

    return errors


def _append_report(report_path: Path, counts: dict[str, int], validation_errors: list[str], urls: list[str]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat()
    status = "pass" if not validation_errors else "fail"
    missing_data = "none"
    parser_errors = "none"

    with report_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## HKJC Results Extraction Run ({timestamp})\n"
            f"- urls: {len(urls)}\n"
            f"- races_rows: {counts['races']}\n"
            f"- runners_rows: {counts['runners']}\n"
            f"- results_rows: {counts['results']}\n"
            f"- dividends_rows: {counts['dividends']}\n"
            f"- validation_status: {status}\n"
            f"- validation_errors: {len(validation_errors)}\n"
            f"- missing_data_log: {missing_data}\n"
            f"- parser_error_log: {parser_errors}\n"
        )
        if validation_errors:
            for error in validation_errors:
                handle.write(f"  - {error}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a small HKJC results extraction sample")
    parser.add_argument("--url", action="append", dest="urls", default=[], help="Specific HKJC local results URL")
    parser.add_argument("--limit", type=int, default=1, help="Number of URLs to auto-discover (default: 1)")
    args = parser.parse_args()

    logs_dir = REPO_ROOT / "logs"
    raw_root = REPO_ROOT / "data" / "raw"
    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"
    report_path = REPO_ROOT / "reports" / "extraction_report.md"

    ensure_log_files(logs_dir)

    urls = args.urls or discover_results_urls(limit=max(args.limit, 1))

    races: list[dict[str, str]] = []
    runners: list[dict[str, str]] = []
    results_rows: list[dict[str, str]] = []
    dividends: list[dict[str, str]] = []

    for source_url in urls:
        fetch_result = fetch_results_page(source_url=source_url, raw_root_dir=raw_root)
        if fetch_result.status_code != 200 or not fetch_result.html.strip():
            log_missing_data(
                logs_dir,
                MissingDataLogEntry(
                    source_name="HKJC",
                    source_url=source_url,
                    source_page_type="Results",
                    entity_type="race_page",
                    entity_key=source_url,
                    missing_field="page_html",
                    reason=f"status_code={fetch_result.status_code}",
                    attempted_action="fetch_results_page",
                    next_action="retry_or_manual_review",
                ),
            )
            continue

        try:
            parsed = parse_results_page(
                html=fetch_result.html,
                source_url=source_url,
                extraction_timestamp=fetch_result.extraction_timestamp,
            )
        except ParserLayoutError as exc:
            append_csv_row(
                logs_dir / "parser_error_log.csv",
                {
                    "source_name": "HKJC",
                    "source_url": source_url,
                    "source_page_type": "Results",
                    "parser_module": "parse_results",
                    "error_type": "parser_failed",
                    "error_message": str(exc),
                    "next_action": "update_parser_layout_mapping",
                },
            )
            continue

        races.extend(parsed.races)
        runners.extend(parsed.runners)
        results_rows.extend(parsed.results)
        try:
            parsed_dividends = parse_dividends_page(
                html=fetch_result.html,
                source_url=source_url,
                extraction_timestamp=fetch_result.extraction_timestamp,
            )
            dividends.extend(parsed_dividends)
        except ParserLayoutError as exc:
            append_csv_row(
                logs_dir / "parser_error_log.csv",
                {
                    "source_name": "HKJC",
                    "source_url": source_url,
                    "source_page_type": "Dividends",
                    "parser_module": "parse_dividends",
                    "error_type": "parser_failed",
                    "error_message": str(exc),
                    "next_action": "update_parser_layout_mapping",
                },
            )

    _write_csv(processed_dir / "races.csv", RACES_COLUMNS, races)
    _write_csv(processed_dir / "runners.csv", RUNNERS_COLUMNS, runners)
    _write_csv(processed_dir / "results.csv", RESULTS_COLUMNS, results_rows)
    _write_csv(processed_dir / "dividends.csv", DIVIDENDS_COLUMNS, dividends)

    validation_errors = _validate_outputs(races, runners, results_rows, dividends)
    if validation_errors:
        for error in validation_errors:
            append_csv_row(
                logs_dir / "parser_error_log.csv",
                {
                    "source_name": "HKJC",
                    "source_url": HKJC_RESULTS_BASE_URL,
                    "source_page_type": "Results",
                    "parser_module": "results_validation",
                    "error_type": "validation_failed",
                    "error_message": error,
                    "next_action": "inspect_processed_outputs",
                },
            )

    counts = {
        "races": len(races),
        "runners": len(runners),
        "results": len(results_rows),
        "dividends": len(dividends),
    }
    _append_report(report_path, counts, validation_errors, urls)

    print(f"urls={len(urls)}")
    print(f"races_rows={counts['races']}")
    print(f"runners_rows={counts['runners']}")
    print(f"results_rows={counts['results']}")
    print(f"dividends_rows={counts['dividends']}")
    print(f"validation_errors={len(validation_errors)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
