from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests

from src.common.raw_archive import archive_raw_content


@dataclass(frozen=True)
class HKHorseDBFetchResult:
    source_url: str
    source_page_type: str
    status: str
    status_code: int
    extraction_timestamp: str
    html: str


_MEMBERSHIP_TOKENS = frozenset(["登入", "會員", "login", "password", "member"])


def _is_access_restricted(html: str) -> bool:
    lower = html.lower()
    return any(token in lower for token in _MEMBERSHIP_TOKENS)


def fetch_hkhorsedb_page(*, source_url: str, source_page_type: str, raw_root_dir: Path) -> HKHorseDBFetchResult:
    timestamp = datetime.now(UTC).isoformat()
    try:
        response = requests.get(source_url, timeout=20, headers={"User-Agent": "hkjc-edge-system/0.1 (https://github.com/Wazzaboy/Wazzaboy; public-data-research)"})
    except requests.RequestException:
        return HKHorseDBFetchResult(
            source_url=source_url,
            source_page_type=source_page_type,
            status="network_unavailable",
            status_code=0,
            extraction_timestamp=timestamp,
            html="",
        )

    status = "public"
    if response.status_code in {401, 403}:
        status = "restricted"
    elif response.status_code != 200:
        status = "error"
    elif _is_access_restricted(response.text):
        # Page returned 200 but contains login/membership content — do not archive
        status = "restricted"

    if status == "public" and response.text:
        archive_raw_content(
            root_dir=raw_root_dir,
            source_name="HKHorseDB",
            source_url=source_url,
            source_page_type=source_page_type,
            raw_bytes=response.content,
        )

    return HKHorseDBFetchResult(
        source_url=source_url,
        source_page_type=source_page_type,
        status=status,
        status_code=response.status_code,
        extraction_timestamp=timestamp,
        html=response.text if status == "public" else "",
    )
