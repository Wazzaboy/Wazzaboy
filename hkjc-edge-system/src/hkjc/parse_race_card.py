from __future__ import annotations

from bs4 import BeautifulSoup


def parse_race_card_page(*, html: str, source_url: str, extraction_timestamp: str) -> list[dict[str, str]]:
    raise NotImplementedError("parse_race_card: not yet implemented")
