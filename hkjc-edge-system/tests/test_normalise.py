from __future__ import annotations

from src.common.normalise import normalise_string
from src.hkhorsedb.normalize import normalize_horse_record


def test_normalise_string_collapses_whitespace() -> None:
    assert normalise_string("  PACKING  KING  ") == "PACKING KING"


def test_normalise_string_replaces_non_breaking_space() -> None:
    assert normalise_string("LUCKY\xa0STAR") == "LUCKY STAR"


def test_normalise_string_nfc_normalisation() -> None:
    # NFC: composed form — café with combining accent should normalise to precomposed
    combining = "café"  # e + combining acute accent
    precomposed = "caf\xe9"   # é precomposed
    assert normalise_string(combining) == precomposed


def test_normalise_string_empty_passthrough() -> None:
    assert normalise_string("") == ""


def test_normalize_horse_record_cleans_string_fields() -> None:
    record = {
        "horse_name": "  HAPPY  HORSE  ",
        "raw_value": "col1\xa0col2",
        "source_url": "https://example.com",
        "source_name": "HKHorseDB",
        "source_page_type": "Horse Database",
        "extraction_timestamp": "2026-01-01T00:00:00Z",
    }
    result = normalize_horse_record(record)
    assert result["horse_name"] == "HAPPY HORSE"
    assert result["raw_value"] == "col1 col2"
    # Provenance fields must be unchanged
    assert result["source_url"] == "https://example.com"
    assert result["extraction_timestamp"] == "2026-01-01T00:00:00Z"
