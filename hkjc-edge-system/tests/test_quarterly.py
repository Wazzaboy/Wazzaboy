from __future__ import annotations

from datetime import date

from src.common.quarterly import count_missing_required_fields, dedupe_rows_by_key, iter_quarter_windows


def test_iter_quarter_windows_splits_range() -> None:
    windows = iter_quarter_windows(date(2026, 1, 15), date(2026, 8, 10))
    assert [(w.start_date.isoformat(), w.end_date.isoformat()) for w in windows] == [
        ("2026-01-15", "2026-03-31"),
        ("2026-04-01", "2026-06-30"),
        ("2026-07-01", "2026-08-10"),
    ]


def test_dedupe_rows_by_key_counts_duplicates() -> None:
    rows = [
        {"race_id": "A", "value": "1"},
        {"race_id": "B", "value": "2"},
        {"race_id": "A", "value": "3"},
    ]
    deduped, duplicates = dedupe_rows_by_key(rows, "race_id")
    assert duplicates == 1
    assert [row["race_id"] for row in deduped] == ["A", "B"]


def test_count_missing_required_fields_treats_null_as_missing() -> None:
    rows = [
        {"source_url": "", "source_name": "HKJC", "source_page_type": "Results", "extraction_timestamp": "2026-01-01T00:00:00Z"},
        {"source_url": "https://x", "source_name": "NULL", "source_page_type": "Results", "extraction_timestamp": ""},
    ]
    assert count_missing_required_fields(rows, ["source_url", "source_name", "extraction_timestamp"]) == 3
