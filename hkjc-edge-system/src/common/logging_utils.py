"""CSV logging helpers for extraction pipeline events."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

MISSING_DATA_COLUMNS = [
    "source_name",
    "source_url",
    "source_page_type",
    "entity_type",
    "entity_key",
    "missing_field",
    "reason",
    "attempted_action",
    "next_action",
    "logged_at",
]

PARSER_ERROR_COLUMNS = [
    "source_name",
    "source_url",
    "source_page_type",
    "parser_module",
    "error_type",
    "error_message",
    "failed_at",
    "next_action",
]

RESTRICTED_PAGE_COLUMNS = [
    "source_name",
    "source_url",
    "source_page_type",
    "restriction_type",
    "access_status",
    "reason",
    "next_action",
    "logged_at",
]

CONFLICT_COLUMNS = [
    "entity_type",
    "entity_key",
    "field_name",
    "hkjc_value",
    "hkjc_source_url",
    "secondary_source_name",
    "secondary_value",
    "secondary_source_url",
    "severity",
    "recommended_resolution",
    "logged_at",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_csv_header(path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()


def append_csv_row(path: Path, columns: list[str], row: Mapping[str, str]) -> None:
    ensure_csv_header(path, columns)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        safe_row = {column: row.get(column, "") for column in columns}
        writer.writerow(safe_row)


def log_missing_data(path: Path, row: Mapping[str, str]) -> None:
    payload = dict(row)
    payload.setdefault("logged_at", utc_now_iso())
    append_csv_row(path, MISSING_DATA_COLUMNS, payload)


def log_parser_error(path: Path, row: Mapping[str, str]) -> None:
    payload = dict(row)
    payload.setdefault("failed_at", utc_now_iso())
    append_csv_row(path, PARSER_ERROR_COLUMNS, payload)


def log_restricted_page(path: Path, row: Mapping[str, str]) -> None:
    payload = dict(row)
    payload.setdefault("logged_at", utc_now_iso())
    append_csv_row(path, RESTRICTED_PAGE_COLUMNS, payload)


def log_conflict(path: Path, row: Mapping[str, str]) -> None:
    payload = dict(row)
    payload.setdefault("logged_at", utc_now_iso())
    append_csv_row(path, CONFLICT_COLUMNS, payload)
