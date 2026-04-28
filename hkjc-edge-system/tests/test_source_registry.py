from __future__ import annotations

from pathlib import Path
import csv

from src.common.source_registry import (
    REQUIRED_SOURCE_FIELDS,
    SourceRegistryEntry,
    default_hkjc_page_groups,
    required_registry_columns,
    write_source_registry,
)


def test_required_registry_columns_include_required_fields() -> None:
    columns = required_registry_columns()
    for field in REQUIRED_SOURCE_FIELDS:
        assert field in columns
    assert "extraction_timestamp" in columns


def test_default_registry_respects_hkjc_priority() -> None:
    entries = default_hkjc_page_groups()
    assert entries[0].source_name == "HKJC"
    assert any(entry.source_name == "HKHorseDB" for entry in entries)
    assert entries[-1].source_name == "HKHorseDB"


def test_write_source_registry_creates_csv(tmp_path: Path) -> None:
    path = tmp_path / "source_registry.csv"
    entries = [
        SourceRegistryEntry(
            source_url="https://racing.hkjc.com/example",
            source_name="HKJC",
            source_page_type="Race Card",
            access_status="public",
            model_value="high",
            leakage_risk="low",
            parser_difficulty="medium",
            notes="sample",
        )
    ]

    write_source_registry(entries, path)

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["source_name"] == "HKJC"
    assert rows[0]["source_page_type"] == "Race Card"
