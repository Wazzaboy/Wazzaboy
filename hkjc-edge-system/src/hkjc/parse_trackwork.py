from __future__ import annotations

from bs4 import BeautifulSoup


def parse_trackwork_page(*, html: str, source_url: str, extraction_timestamp: str) -> list[dict[str, str]]:
    raise NotImplementedError("parse_trackwork: not yet implemented")
