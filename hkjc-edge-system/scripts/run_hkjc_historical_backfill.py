#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
import sys
import time
import argparse

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import requests
from bs4 import BeautifulSoup

from src.common.logging_utils import MissingDataLogEntry, append_csv_row, ensure_log_files, log_missing_data
from src.common.raw_archive import archive_raw_content
from src.hkjc.parse_dividends import parse_dividends_page
from src.hkjc.parse_results import ParserLayoutError, parse_results_page

PACE_SECONDS = 0.35

COMMENTS_COLUMNS = [
    "source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id", "runner_id",
    "horse_no", "horse_name", "comment_type", "comment_text", "post_race_only", "raw_value",
]
INCIDENT_COLUMNS = [
    "source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id",
    "incident_report_url", "incident_report_available", "status", "raw_value", "post_race_only",
]
RACE_CARD_COLUMNS = [
    "source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id",
    "race_card_url", "race_card_available", "status", "raw_value",
]
CHANGES_COLUMNS = [
    "source_url", "source_name", "source_page_type", "extraction_timestamp", "race_id",
    "changes_url", "changes_available", "status", "raw_value",
]


def _load_race_index(path: Path, start_date: str, end_date: str) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    filtered = [
        row
        for row in rows
        if start_date <= row.get("race_date", "") <= end_date
        and row.get("result_available", "").lower() == "true"
        and row.get("racecourse", "") in {"ST", "HV"}
    ]
    filtered.sort(key=lambda row: (row.get("race_date", ""), row.get("racecourse", ""), int(row.get("race_no", "999") or 999)))
    return filtered


def _parse_comments(page_html: str, source_url: str, extraction_timestamp: str, race_id: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(page_html, "html.parser")
    comment_tables = soup.select("table.f_tac.table_bd")
    if not comment_tables:
        return []

    table = comment_tables[-1]
    rows: list[dict[str, str]] = []
    for tr in table.select("tr")[1:]:
        cells = [" ".join(td.get_text(" ", strip=True).split()) for td in tr.select("td")]
        if len(cells) < 4:
            continue
        horse_no = cells[1]
        horse_name = cells[2]
        runner_id = f"{race_id}-{horse_no}" if race_id and horse_no else ""
        rows.append(
            {
                "source_url": source_url,
                "source_name": "HKJC",
                "source_page_type": "Comments on Running",
                "extraction_timestamp": extraction_timestamp,
                "race_id": race_id,
                "runner_id": runner_id,
                "horse_no": horse_no,
                "horse_name": horse_name,
                "comment_type": "incident",
                "comment_text": cells[3],
                "post_race_only": "true",
                "raw_value": "|".join(cells),
            }
        )
    return rows


def _write(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def _append_report(
    path: Path,
    summary: dict[str, int],
    missing_count: int,
    parser_failures: int,
    index_start: str,
    index_end: str,
    requested_start: str,
    requested_end: str,
) -> None:
    timestamp = datetime.now(UTC).isoformat()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## Controlled Historical Backfill ({timestamp})\n"
            f"- total_races_processed: {summary['races']}\n"
            f"- total_runner_rows: {summary['runners']}\n"
            f"- total_result_rows: {summary['results']}\n"
            f"- total_dividend_rows: {summary['dividends']}\n"
            f"- total_comments_rows: {summary['comments']}\n"
            f"- total_incident_rows: {summary['incidents']}\n"
            f"- missing_data_rows: {missing_count}\n"
            f"- parser_failures: {parser_failures}\n"
            f"- modeling_ready: no\n"
            f"- requested_range: {requested_start} to {requested_end}\n"
            f"- index_coverage_range: {index_start} to {index_end}\n"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run controlled HKJC historical backfill from race_index.csv")
    parser.add_argument("--start-date", default="2020-01-01", help="Inclusive YYYY-MM-DD")
    parser.add_argument("--end-date", default=datetime.now(UTC).date().isoformat(), help="Inclusive YYYY-MM-DD")
    args = parser.parse_args()

    race_index_path = REPO_ROOT / "data" / "processed" / "hkjc" / "race_index.csv"
    if not race_index_path.exists():
        raise SystemExit(f"race_index.csv not found: {race_index_path}")

    logs_dir = REPO_ROOT / "logs"
    ensure_log_files(logs_dir)

    with race_index_path.open("r", newline="", encoding="utf-8") as handle:
        all_index_rows = list(csv.DictReader(handle))
    index_dates = sorted([row.get("race_date", "") for row in all_index_rows if row.get("race_date")])
    index_start = index_dates[0] if index_dates else "NULL"
    index_end = index_dates[-1] if index_dates else "NULL"

    race_rows = _load_race_index(race_index_path, args.start_date, args.end_date)
    raw_root = REPO_ROOT / "data" / "raw"
    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"

    all_races: list[dict[str, str]] = []
    all_runners: list[dict[str, str]] = []
    all_results: list[dict[str, str]] = []
    all_dividends: list[dict[str, str]] = []
    all_comments: list[dict[str, str]] = []
    all_incidents: list[dict[str, str]] = []
    all_race_cards: list[dict[str, str]] = []
    all_changes: list[dict[str, str]] = []

    parser_failures = 0

    for idx, race in enumerate(race_rows, start=1):
        result_url = race.get("result_url", "")
        if not result_url:
            continue

        extraction_timestamp = datetime.now(UTC).isoformat()
        try:
            response = requests.get(result_url, timeout=20, headers={"User-Agent": "hkjc-edge-system/0.1 (+historical-backfill)"})
        except requests.RequestException as exc:
            log_missing_data(
                logs_dir,
                MissingDataLogEntry(
                    source_name="HKJC",
                    source_url=result_url,
                    source_page_type="Results",
                    entity_type="race_page",
                    entity_key=race.get("race_id", result_url),
                    missing_field="page_html",
                    reason=f"request_failed:{exc.__class__.__name__}",
                    attempted_action="historical_backfill.fetch",
                    next_action="retry",
                ),
            )
            continue

        if response.status_code in {401, 403}:
            append_csv_row(
                logs_dir / "restricted_pages_log.csv",
                {
                    "source_name": "HKJC",
                    "source_url": result_url,
                    "source_page_type": "Results",
                    "restriction_type": "http_status",
                    "access_status": str(response.status_code),
                    "reason": "access_restricted",
                    "next_action": "skip",
                },
            )
            continue

        if response.status_code != 200 or not response.text.strip():
            log_missing_data(
                logs_dir,
                MissingDataLogEntry(
                    source_name="HKJC",
                    source_url=result_url,
                    source_page_type="Results",
                    entity_type="race_page",
                    entity_key=race.get("race_id", result_url),
                    missing_field="page_html",
                    reason=f"status_code={response.status_code}",
                    attempted_action="historical_backfill.fetch",
                    next_action="retry",
                ),
            )
            continue

        archive_raw_content(
            root_dir=raw_root,
            source_name="HKJC",
            source_url=result_url,
            source_page_type="Results",
            raw_bytes=response.content,
        )

        try:
            parsed = parse_results_page(html=response.text, source_url=result_url, extraction_timestamp=extraction_timestamp)
            dividends = parse_dividends_page(html=response.text, source_url=result_url, extraction_timestamp=extraction_timestamp)
            comments = _parse_comments(response.text, result_url, extraction_timestamp, parsed.races[0].get("race_id", ""))
        except ParserLayoutError as exc:
            parser_failures += 1
            append_csv_row(
                logs_dir / "parser_error_log.csv",
                {
                    "source_name": "HKJC",
                    "source_url": result_url,
                    "source_page_type": "Results",
                    "parser_module": "historical_backfill",
                    "error_type": "parser_failed",
                    "error_message": str(exc),
                    "next_action": "manual_layout_review",
                },
            )
            continue

        all_races.extend(parsed.races)
        all_runners.extend(parsed.runners)
        all_results.extend(parsed.results)
        all_dividends.extend(dividends)
        all_comments.extend(comments)

        race_id = parsed.races[0].get("race_id", "")
        all_incidents.append(
            {
                "source_url": result_url,
                "source_name": "HKJC",
                "source_page_type": "Incident Report",
                "extraction_timestamp": extraction_timestamp,
                "race_id": race_id,
                "incident_report_url": race.get("incident_report_url", "NULL"),
                "incident_report_available": race.get("incident_report_available", "false"),
                "status": "linked" if race.get("incident_report_available", "false") == "true" else "not_available",
                "raw_value": race.get("incident_report_url", ""),
                "post_race_only": "true",
            }
        )
        all_race_cards.append(
            {
                "source_url": result_url,
                "source_name": "HKJC",
                "source_page_type": "Race Card",
                "extraction_timestamp": extraction_timestamp,
                "race_id": race_id,
                "race_card_url": race.get("race_card_url", "NULL"),
                "race_card_available": race.get("race_card_available", "false"),
                "status": "linked" if race.get("race_card_available", "false") == "true" else "not_available",
                "raw_value": race.get("race_card_url", ""),
            }
        )
        all_changes.append(
            {
                "source_url": result_url,
                "source_name": "HKJC",
                "source_page_type": "Changes",
                "extraction_timestamp": extraction_timestamp,
                "race_id": race_id,
                "changes_url": "NULL",
                "changes_available": "false",
                "status": "not_collected",
                "raw_value": "",
            }
        )

        if idx % 25 == 0:
            print(f"processed={idx}/{len(race_rows)}")
        time.sleep(PACE_SECONDS)

    # write core tables
    from scripts.run_hkjc_results_extraction import RACES_COLUMNS, RUNNERS_COLUMNS, RESULTS_COLUMNS, DIVIDENDS_COLUMNS

    _write(processed_dir / "races.csv", all_races, RACES_COLUMNS)
    _write(processed_dir / "runners.csv", all_runners, RUNNERS_COLUMNS)
    _write(processed_dir / "results.csv", all_results, RESULTS_COLUMNS)
    _write(processed_dir / "dividends.csv", all_dividends, DIVIDENDS_COLUMNS)
    _write(processed_dir / "comments.csv", all_comments, COMMENTS_COLUMNS)
    _write(processed_dir / "incidents.csv", all_incidents, INCIDENT_COLUMNS)
    _write(processed_dir / "race_cards.csv", all_race_cards, RACE_CARD_COLUMNS)
    _write(processed_dir / "changes.csv", all_changes, CHANGES_COLUMNS)

    # summaries
    missing_count = 0
    with (logs_dir / "missing_data_log.csv").open("r", newline="", encoding="utf-8") as handle:
        missing_count = max(sum(1 for _ in handle) - 1, 0)

    _append_report(
        REPO_ROOT / "reports" / "extraction_report.md",
        {
            "races": len(all_races),
            "runners": len(all_runners),
            "results": len(all_results),
            "dividends": len(all_dividends),
            "comments": len(all_comments),
            "incidents": len(all_incidents),
        },
        missing_count,
        parser_failures,
        index_start=index_start,
        index_end=index_end,
        requested_start=args.start_date,
        requested_end=args.end_date,
    )

    print(f"total_races_processed={len(all_races)}")
    print(f"total_runner_rows={len(all_runners)}")
    print(f"total_dividend_rows={len(all_dividends)}")
    print(f"total_comments_rows={len(all_comments)}")
    print(f"total_incident_rows={len(all_incidents)}")
    print(f"missingness_summary_rows={missing_count}")
    print(f"parser_failure_summary={parser_failures}")
    print(f"requested_range={args.start_date}:{args.end_date}")
    print(f"index_coverage_range={index_start}:{index_end}")
    print("modeling_ready=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
