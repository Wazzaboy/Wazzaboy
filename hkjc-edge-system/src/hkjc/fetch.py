from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.common.raw_archive import RawArchiveRecord, archive_raw_content

HKJC_RESULTS_BASE_URL = "https://racing.hkjc.com/en-us/local/information/localresults"
_USER_AGENT = "hkjc-edge-system/0.1 (https://github.com/Wazzaboy/Wazzaboy; public-data-research)"


@dataclass(frozen=True)
class FetchResult:
    source_url: str
    status_code: int
    extraction_timestamp: str
    html: str
    archive_record: RawArchiveRecord | None


def discover_results_urls(
    *,
    base_url: str = HKJC_RESULTS_BASE_URL,
    limit: int = 1,
    timeout_seconds: int = 20,
) -> list[str]:
    try:
        response = requests.get(
            base_url,
            timeout=timeout_seconds,
            headers={"User-Agent": _USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException:
        return [base_url]

    soup = BeautifulSoup(response.text, "html.parser")
    urls: list[str] = []
    for anchor in soup.select("a[href*='localresults?racedate=']"):
        href = anchor.get("href")
        if not href:
            continue
        absolute = urljoin(base_url, href)
        if absolute not in urls:
            urls.append(absolute)
        if len(urls) >= limit:
            break

    if not urls:
        urls.append(base_url)
    return urls


def fetch_results_page(
    *,
    source_url: str,
    raw_root_dir: Path,
    timeout_seconds: int = 20,
    polite_delay_seconds: float = 0.0,
) -> FetchResult:
    if polite_delay_seconds > 0:
        sleep(polite_delay_seconds)

    try:
        response = requests.get(
            source_url,
            timeout=timeout_seconds,
            headers={"User-Agent": _USER_AGENT},
        )
    except requests.RequestException as exc:
        timestamp = datetime.now(UTC).isoformat()
        return FetchResult(
            source_url=source_url,
            status_code=0,
            extraction_timestamp=timestamp,
            html="",
            archive_record=None,
        )

    timestamp = datetime.now(UTC).isoformat()

    archive_record: RawArchiveRecord | None = None
    if response.ok and response.text:
        archive_record = archive_raw_content(
            root_dir=raw_root_dir,
            source_name="HKJC",
            source_url=source_url,
            source_page_type="Results",
            raw_bytes=response.content,
        )

    return FetchResult(
        source_url=source_url,
        status_code=response.status_code,
        extraction_timestamp=timestamp,
        html=response.text,
        archive_record=archive_record,
    )
