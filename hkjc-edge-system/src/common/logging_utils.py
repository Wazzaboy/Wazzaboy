from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
import csv
from typing import Any


REQUIRED_LOG_COLUMNS: dict[str, list[str]] = {
    "missing_data_log.csv": [
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
    ],
    "parser_error_log.csv": [
        "source_name",
        "source_url",
        "source_page_type",
        "parser_module",
        "error_type",
        "error_message",
        "failed_at",
        "next_action",
    ],
    "restricted_pages_log.csv": [
        "source_name",
        "source_url",
        "source_page_type",
        "restriction_type",
        "access_status",
        "reason",
        "next_action",
        "logged_at",
    ],
    "conflict_log.csv": [
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
    ],
}


@dataclass(frozen=True)
class MissingDataLogEntry:
    source_name: str
    source_url: str
    source_page_type: str
    entity_type: str
    entity_key: str
    missing_field: str
    reason: str
    attempted_action: str
    next_action: str
    logged_at: str = ""


def ensure_log_files(logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    for filename, columns in REQUIRED_LOG_COLUMNS.items():
        path = logs_dir / filename
        if path.exists() and path.stat().st_size > 0:
            continue
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()


def append_csv_row(path: Path, row: dict[str, Any]) -> None:
    columns = REQUIRED_LOG_COLUMNS.get(path.name)
    if not columns:
        raise ValueError(f"Unsupported log file: {path.name}")

    if not path.exists() or path.stat().st_size == 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()

    normalized = {key: row.get(key, "") for key in columns}
    if "logged_at" in normalized and not normalized["logged_at"]:
        normalized["logged_at"] = datetime.now(UTC).isoformat()
    if "failed_at" in normalized and not normalized["failed_at"]:
        normalized["failed_at"] = datetime.now(UTC).isoformat()

    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writerow(normalized)


def log_missing_data(logs_dir: Path, entry: MissingDataLogEntry) -> None:
    append_csv_row(logs_dir / "missing_data_log.csv", asdict(entry))
