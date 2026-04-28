from __future__ import annotations

from src.common.normalise import normalise_string


def normalize_horse_record(record: dict[str, str]) -> dict[str, str]:
    """Apply string normalisation to all string fields in a HKHorseDB record.

    Non-string values are passed through unchanged. Provenance fields
    (source_url, source_name, source_page_type, extraction_timestamp) are
    preserved verbatim.
    """
    _VERBATIM = frozenset({"source_url", "source_name", "source_page_type", "extraction_timestamp"})
    return {
        key: (value if key in _VERBATIM else normalise_string(value))
        for key, value in record.items()
    }
