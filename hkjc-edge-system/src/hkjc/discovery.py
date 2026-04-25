"""HKJC source discovery (public pages only)."""

from __future__ import annotations

import csv
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.common.logging_utils import log_parser_error, log_restricted_page
from src.common.source_registry import DISCOVERY_REQUIRED_FIELDS, HKJC_PAGES


USER_AGENT = "hkjc-edge-system/0.1 (+public-source-discovery)"


def _status_to_access_status(status_code: int) -> str:
    if status_code in {401, 403, 451}:
        return "restricted"
    if 200 <= status_code < 400:
        return "public"
    return "unavailable"


def discover_hkjc_public_pages(timeout_seconds: float = 15.0) -> list[dict[str, str]]:
    """Discover HKJC page-group accessibility without bypassing protections."""
    discovered: list[dict[str, str]] = []

    for page in HKJC_PAGES:
        request = Request(page.source_url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310 (public read-only URL discovery)
                status_code = response.status
            access_status = _status_to_access_status(status_code)
            note = f"http_status={status_code}"
            row = replace(page, access_status=access_status, notes=f"{page.notes} [{note}]")
        except HTTPError as exc:
            access_status = _status_to_access_status(exc.code)
            row = replace(page, access_status=access_status, notes=f"{page.notes} [http_status={exc.code}]")
        except URLError as exc:
            row = replace(page, access_status="network_unavailable", notes=f"{page.notes} [network_error={exc.reason}]")
        discovered.append(asdict(row))

    return discovered


def persist_discovery(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DISCOVERY_REQUIRED_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in DISCOVERY_REQUIRED_FIELDS})


def audit_discovery(rows: list[dict[str, str]], logs_dir: Path) -> None:
    for row in rows:
        if row["access_status"] == "restricted":
            log_restricted_page(
                logs_dir / "restricted_pages_log.csv",
                {
                    "source_name": row["source_name"],
                    "source_url": row["source_url"],
                    "source_page_type": row["source_page_type"],
                    "restriction_type": "http_access_control",
                    "access_status": row["access_status"],
                    "reason": row["notes"],
                    "next_action": "manual_review_only",
                },
            )
        if row["access_status"] == "network_unavailable":
            log_parser_error(
                logs_dir / "parser_error_log.csv",
                {
                    "source_name": row["source_name"],
                    "source_url": row["source_url"],
                    "source_page_type": row["source_page_type"],
                    "parser_module": "hkjc.discovery",
                    "error_type": "network_unavailable",
                    "error_message": row["notes"],
                    "next_action": "retry_later",
                },
            )


def discovery_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for row in rows:
        statuses[row["access_status"]] = statuses.get(row["access_status"], 0) + 1
    return {"row_count": len(rows), "status_counts": statuses}
