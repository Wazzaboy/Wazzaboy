from src.common.source_registry import get_source, is_primary_source, validate_source_url


def test_get_source_hkjc() -> None:
    source = get_source("hkjc")
    assert source.priority == 1
    assert "racing.hkjc.com" in source.domains


def test_validate_source_url() -> None:
    assert validate_source_url("HKJC", "https://racing.hkjc.com/racing/information")
    assert not validate_source_url("HKJC", "https://example.com/page")


def test_is_primary_source() -> None:
    assert is_primary_source("HKJC")
    assert not is_primary_source("HKHORSEDB")
