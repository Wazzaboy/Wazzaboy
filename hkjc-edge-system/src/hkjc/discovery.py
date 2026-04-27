from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from time import sleep
import csv

import requests

from src.common.source_registry import (
    SourceRegistryEntry,
    default_hkjc_page_groups,
    required_registry_columns,
    write_source_registry,
)
from src.common.validation import validate_source_registry_rows, validation_summary


def _probe_access_status(url: str, timeout_seconds: int = 12) -> tuple[str, str]:
    try:
        response = requests.get(
            url,
            timeout=timeout_seconds,
            headers={"User-Agent": "hkjc-edge-system/0.1 (+public-source-discovery)"},
        )
    except requests.RequestException as exc:
        return "network_unavailable", f"request failed: {exc.__class__.__name__}"

    if response.status_code in {401, 403}:
        return "restricted", f"status_code={response.status_code}"
    if response.status_code >= 500:
        return "error", f"status_code={response.status_code}"
    if response.status_code == 404:
        return "error", "status_code=404"
    return "public", f"status_code={response.status_code}"


def discover_sources(polite_delay_seconds: float = 0.5) -> list[SourceRegistryEntry]:
    discovered: list[SourceRegistryEntry] = []
    now = datetime.now(UTC).isoformat()

    for entry in default_hkjc_page_groups():
        updated = entry
        if entry.source_name == "HKJC":
            access_status, probe_note = _probe_access_status(entry.source_url)
            note = f"{entry.notes} | discovery_probe={probe_note}" if entry.notes else probe_note
            updated = replace(
                entry,
                access_status=access_status,
                notes=note,
                extraction_timestamp=now,
            )
            sleep(polite_delay_seconds)
        else:
            updated = replace(entry, extraction_timestamp=now)
        discovered.append(updated)

    return discovered


def write_discovery_outputs(
    entries: list[SourceRegistryEntry],
    registry_path: Path,
    validation_path: Path,
) -> tuple[str, int]:
    write_source_registry(entries, registry_path)

    rows = [entry.to_dict() for entry in entries]
    issues = validate_source_registry_rows(rows)
    summary = validation_summary(issues)

    validation_path.parent.mkdir(parents=True, exist_ok=True)
    with validation_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["status", "issue_count", "row_index", "field", "message"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "status": summary,
                "issue_count": len(issues),
                "row_index": "",
                "field": "",
                "message": "",
            }
        )
        for issue in issues:
            writer.writerow(
                {
                    "status": "issue",
                    "issue_count": len(issues),
                    "row_index": issue.row_index,
                    "field": issue.field,
                    "message": issue.message,
                }
            )

    return summary, len(issues)


def source_registry_sample(path: Path, limit: int = 5) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, fieldnames=required_registry_columns())
        next(reader, None)
        for idx, row in enumerate(reader):
            rows.append(row)
            if idx + 1 >= limit:
                break
    return rows
