from src.common.source_registry import (
    DISCOVERY_REQUIRED_FIELDS,
    get_source,
    is_primary_source,
    source_pages_as_rows,
    validate_source_url,
)


def test_hkjc_is_primary() -> None:
    assert is_primary_source("HKJC")
    assert not is_primary_source("HKHORSEDB")


def test_source_url_validation() -> None:
    assert validate_source_url("HKJC", "https://racing.hkjc.com/racing/information/English/racing/Racecard.aspx")
    assert not validate_source_url("HKJC", "https://example.com/page")


def test_discovery_row_fields_present() -> None:
    rows = source_pages_as_rows("HKJC")
    assert rows
    for field in DISCOVERY_REQUIRED_FIELDS:
        assert field in rows[0]


def test_hkhorsedb_secondary_placeholder() -> None:
    source = get_source("HKHORSEDB")
    assert source.priority == 2
    assert source.source_type == "secondary"
