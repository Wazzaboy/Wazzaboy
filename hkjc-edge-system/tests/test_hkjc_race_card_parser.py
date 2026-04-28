from __future__ import annotations

import pytest

from src.hkjc.parse_race_card import parse_race_card_page


def test_parse_race_card_page_not_yet_implemented() -> None:
    with pytest.raises(NotImplementedError):
        parse_race_card_page(html="<html/>", source_url="https://example.com", extraction_timestamp="2026-01-01T00:00:00Z")
