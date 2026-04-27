from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import csv
import requests
from bs4 import BeautifulSoup

from src.common.logging_utils import MissingDataLogEntry, log_missing_data
from src.hkjc.fetch import HKJC_RESULTS_BASE_URL, fetch_results_page
from src.hkjc.parse_results import ParserLayoutError, parse_results_page


RACE_INDEX_COLUMNS = [
    "source_url",
    "source_name",
    "extraction_timestamp",
    "race_date",
    "racecourse",
    "race_no",
    "race_name",
    "class",
    "distance",
    "surface",
    "result_url",
    "result_available",
    "race_card_url",
    "race_card_available",
    "comments_url",
    "comments_available",
    "incident_report_url",
    "incident_report_available",
    "notes",
]


@dataclass(frozen=True)
class RaceIndexBuildStats:
    rows: int
    missing_field_count: int
    skipped_dates: int


def _date_to_hkjc_string(target_date: date) -> str:
    return target_date.strftime("%Y/%m/%d")


def _null(value: str) -> str:
    return value if value else "NULL"


def build_date_results_url(target_date: date) -> str:
    return f"{HKJC_RESULTS_BASE_URL}?{urlencode({'racedate': _date_to_hkjc_string(target_date)})}"


def _extract_anchor_url(base_url: str, href: str) -> str:
    return urljoin(base_url, href)


def extract_race_result_urls_from_date_page(*, html: str, requested_date: date, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    date_key = _date_to_hkjc_string(requested_date)

    for anchor in soup.select("a[href*='localresults?racedate=']"):
        href = anchor.get("href")
        if not href:
            continue
        full_url = _extract_anchor_url(base_url, href)
        query = parse_qs(urlparse(full_url).query)
        racedate = query.get("racedate", [""])[0]
        race_no = query.get("RaceNo", [""])[0]
        racecourse = query.get("Racecourse", [""])[0]
        if racedate != date_key:
            continue
        if not race_no or not racecourse:
            continue
        if full_url not in urls:
            urls.append(full_url)

    return urls


def _extract_related_link(soup: BeautifulSoup, keyword: str, page_url: str) -> tuple[str, str]:
    for anchor in soup.select("a[href]"):
        text = " ".join(anchor.get_text(" ", strip=True).split()).lower()
        if keyword.lower() in text:
            href = anchor.get("href", "")
            if not href:
                continue
            return _extract_anchor_url(page_url, href), "true"
    return "NULL", "false"


def _to_row(*, page_html: str, result_url: str, extraction_timestamp: str, requested_date: date) -> tuple[dict[str, str], int]:
    soup = BeautifulSoup(page_html, "html.parser")
    parsed = parse_results_page(html=page_html, source_url=result_url, extraction_timestamp=extraction_timestamp)
    race = parsed.races[0]

    race_card_url, race_card_available = _extract_related_link(soup, "race card", result_url)
    comments_url, comments_available = _extract_related_link(soup, "comments on running", result_url)
    incident_url, incident_available = _extract_related_link(soup, "incident report", result_url)

    row = {
        "source_url": result_url,
        "source_name": "HKJC",
        "extraction_timestamp": extraction_timestamp,
        "race_date": _null(race.get("race_date", "")),
        "racecourse": _null(race.get("racecourse", "")),
        "race_no": _null(race.get("race_no", "")),
        "race_name": _null(race.get("race_name", "")),
        "class": _null(race.get("class", "")),
        "distance": _null(race.get("distance", "")),
        "surface": _null(race.get("surface", "")),
        "result_url": result_url,
        "result_available": "true",
        "race_card_url": race_card_url,
        "race_card_available": race_card_available,
        "comments_url": comments_url,
        "comments_available": comments_available,
        "incident_report_url": incident_url,
        "incident_report_available": incident_available,
        "notes": "",
    }

    missing_fields = [key for key, value in row.items() if value == "NULL" and key not in {"surface", "race_card_url", "comments_url", "incident_report_url"}]
    if row["race_date"] != requested_date.strftime("%Y-%m-%d"):
        row["notes"] = f"race_date_mismatch_requested={requested_date.isoformat()}"

    return row, len(missing_fields)


def write_race_index(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RACE_INDEX_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "NULL") for col in RACE_INDEX_COLUMNS})


def build_race_index(
    *,
    start_date: date,
    end_date: date,
    output_path: Path,
    raw_root_dir: Path,
    logs_dir: Path,
    request_timeout_seconds: int = 20,
    polite_delay_seconds: float = 0.5,
) -> RaceIndexBuildStats:
    today = datetime.now(UTC).date()
    effective_end = min(end_date, today)

    rows: list[dict[str, str]] = []
    missing_field_count = 0
    skipped_dates = 0

    cursor = start_date
    while cursor <= effective_end:
        date_url = build_date_results_url(cursor)
        try:
            date_response = requests.get(date_url, timeout=request_timeout_seconds)
        except requests.RequestException as exc:
            skipped_dates += 1
            log_missing_data(
                logs_dir,
                MissingDataLogEntry(
                    source_name="HKJC",
                    source_url=date_url,
                    source_page_type="Results",
                    entity_type="race_date",
                    entity_key=cursor.isoformat(),
                    missing_field="date_page_html",
                    reason=f"request_failed:{exc.__class__.__name__}",
                    attempted_action="build_race_index.fetch_date_page",
                    next_action="retry",
                ),
            )
            cursor += timedelta(days=1)
            continue

        if date_response.status_code != 200:
            skipped_dates += 1
            log_missing_data(
                logs_dir,
                MissingDataLogEntry(
                    source_name="HKJC",
                    source_url=date_url,
                    source_page_type="Results",
                    entity_type="race_date",
                    entity_key=cursor.isoformat(),
                    missing_field="date_page_html",
                    reason=f"status_code={date_response.status_code}",
                    attempted_action="build_race_index.fetch_date_page",
                    next_action="retry",
                ),
            )
            cursor += timedelta(days=1)
            continue

        race_urls = extract_race_result_urls_from_date_page(
            html=date_response.text,
            requested_date=cursor,
            base_url=date_url,
        )

        if not race_urls:
            skipped_dates += 1
            cursor += timedelta(days=1)
            continue

        for race_url in race_urls:
            fetched = fetch_results_page(source_url=race_url, raw_root_dir=raw_root_dir, timeout_seconds=request_timeout_seconds, polite_delay_seconds=polite_delay_seconds)
            if fetched.status_code != 200 or not fetched.html.strip():
                log_missing_data(
                    logs_dir,
                    MissingDataLogEntry(
                        source_name="HKJC",
                        source_url=race_url,
                        source_page_type="Results",
                        entity_type="race_page",
                        entity_key=race_url,
                        missing_field="page_html",
                        reason=f"status_code={fetched.status_code}",
                        attempted_action="build_race_index.fetch_results_page",
                        next_action="retry",
                    ),
                )
                continue

            try:
                row, missing_count = _to_row(
                    page_html=fetched.html,
                    result_url=race_url,
                    extraction_timestamp=fetched.extraction_timestamp,
                    requested_date=cursor,
                )
                rows.append(row)
                missing_field_count += missing_count
            except ParserLayoutError:
                log_missing_data(
                    logs_dir,
                    MissingDataLogEntry(
                        source_name="HKJC",
                        source_url=race_url,
                        source_page_type="Results",
                        entity_type="race_page",
                        entity_key=race_url,
                        missing_field="race_metadata",
                        reason="parser_failed",
                        attempted_action="build_race_index.parse_results_page",
                        next_action="manual_layout_review",
                    ),
                )

        cursor += timedelta(days=1)

    rows.sort(key=lambda row: (row["race_date"], row["racecourse"], int(row["race_no"]) if row["race_no"].isdigit() else 999))
    write_race_index(rows, output_path)
    return RaceIndexBuildStats(rows=len(rows), missing_field_count=missing_field_count, skipped_dates=skipped_dates)
