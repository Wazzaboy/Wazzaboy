from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class QuarterWindow:
    start_date: date
    end_date: date


def iter_quarter_windows(start_date: date, end_date: date) -> list[QuarterWindow]:
    if end_date < start_date:
        raise ValueError("end_date must be on/after start_date")

    windows: list[QuarterWindow] = []
    cursor = start_date
    while cursor <= end_date:
        quarter = ((cursor.month - 1) // 3) + 1
        quarter_end_month = quarter * 3
        quarter_end_day = calendar.monthrange(cursor.year, quarter_end_month)[1]
        quarter_end = date(cursor.year, quarter_end_month, quarter_end_day)

        window_end = quarter_end if quarter_end <= end_date else end_date
        windows.append(QuarterWindow(start_date=cursor, end_date=window_end))
        if window_end == end_date:
            break

        next_month = quarter_end_month + 1
        next_year = cursor.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        cursor = date(next_year, next_month, 1)

    return windows


def dedupe_rows_by_key(rows: Iterable[dict[str, str]], key_field: str) -> tuple[list[dict[str, str]], int]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    duplicates = 0
    for row in rows:
        key = row.get(key_field, "")
        if not key:
            deduped.append(row)
            continue
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        deduped.append(row)
    return deduped, duplicates


def count_missing_required_fields(rows: Iterable[dict[str, str]], required_fields: list[str]) -> int:
    missing = 0
    for row in rows:
        for field in required_fields:
            value = (row.get(field, "") or "").strip()
            if value in {"", "NULL"}:
                missing += 1
    return missing
