from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import csv

import requests
from bs4 import BeautifulSoup

from src.common.logging_utils import append_csv_row


@dataclass(frozen=True)
class HKHorseDBSource:
    source_url: str
    source_name: str
    source_page_type: str
    access_status: str
    model_value: str
    leakage_risk: str
    parser_difficulty: str
    notes: str
    extraction_timestamp: str


REGISTRY_COLUMNS = [
    "source_url",
    "source_name",
    "source_page_type",
    "access_status",
    "model_value",
    "leakage_risk",
    "parser_difficulty",
    "notes",
    "extraction_timestamp",
]

FACTOR_COLUMNS = [
    "factor_name",
    "source_name",
    "source_section",
    "source_url",
    "available",
    "pre_race_usable",
    "post_race_only",
    "leakage_risk",
    "model_value",
    "extraction_priority",
]


def _is_membership_restricted(html: str) -> bool:
    lower = html.lower()
    return any(token in lower for token in ["登入", "會員", "login", "password", "member"])


def discover_hkhorsedb_sources(logs_dir: Path) -> list[HKHorseDBSource]:
    candidates = [
        ("https://www.hkhorsedb.com/", "Landing"),
        ("https://www.hkhorsedb.com/cseh/index.php", "Horse Database"),
        ("https://www.hkhorsedb.com/cseh/user.php", "Member Login"),
    ]

    timestamp = datetime.now(UTC).isoformat()
    entries: list[HKHorseDBSource] = []

    for url, page_type in candidates:
        access_status = "unknown"
        note = ""
        try:
            response = requests.get(url, timeout=20, headers={"User-Agent": "hkjc-edge-system/0.1 (+secondary-discovery)"})
            if response.status_code in {401, 403}:
                access_status = "restricted"
                note = f"status_code={response.status_code}"
            elif _is_membership_restricted(response.text):
                access_status = "restricted"
                note = "membership_or_login_detected"
            elif response.status_code == 200:
                access_status = "public"
                note = "public_page_detected"
            else:
                access_status = "error"
                note = f"status_code={response.status_code}"
        except requests.RequestException as exc:
            access_status = "network_unavailable"
            note = f"request_failed:{exc.__class__.__name__}"

        if access_status == "restricted":
            append_csv_row(
                logs_dir / "restricted_pages_log.csv",
                {
                    "source_name": "HKHorseDB",
                    "source_url": url,
                    "source_page_type": page_type,
                    "restriction_type": "membership_or_access",
                    "access_status": access_status,
                    "reason": note,
                    "next_action": "do_not_bypass",
                },
            )

        entries.append(
            HKHorseDBSource(
                source_url=url,
                source_name="HKHorseDB",
                source_page_type=page_type,
                access_status=access_status,
                model_value="secondary",
                leakage_risk="review_required",
                parser_difficulty="medium",
                notes=note,
                extraction_timestamp=timestamp,
            )
        )

    return entries


def write_source_registry(entries: list[HKHorseDBSource], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_COLUMNS)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry.__dict__)


def write_factor_availability(entries: list[HKHorseDBSource], output_path: Path) -> None:
    rows = [
        {
            "factor_name": "horse_profile_enrichment",
            "source_name": "HKHorseDB",
            "source_section": entry.source_page_type,
            "source_url": entry.source_url,
            "available": "true" if entry.access_status == "public" else "false",
            "pre_race_usable": "false",
            "post_race_only": "false",
            "leakage_risk": "review_required",
            "model_value": "secondary",
            "extraction_priority": "low",
        }
        for entry in entries
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FACTOR_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
