#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "hkjc"
NORMAL_TABLES = [
    "runners.csv",
    "results.csv",
    "feature_store.csv",
    "model_probabilities.csv",
    "betting_ev_simulation.csv",
]
ABNORMAL_FIELDS = [
    "source_url",
    "source_name",
    "source_page_type",
    "extraction_timestamp",
    "race_id",
    "race_date",
    "racecourse",
    "race_no",
    "runner_id",
    "horse_no",
    "horse_name",
    "horse_id_or_brand_no",
    "abnormal_reason",
    "raw_value",
]


def _blank(value: object) -> bool:
    return str(value if value is not None else "").strip() in {"", "NULL", "nan", "NaN"}


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _abnormal_from(table_name: str, row: dict[str, str]) -> dict[str, str]:
    return {
        "source_url": row.get("source_url") or row.get("source_url_runner") or "",
        "source_name": row.get("source_name") or row.get("source_name_runner") or "HKJC",
        "source_page_type": row.get("source_page_type") or row.get("source_page_type_runner") or "ProcessedOutput",
        "extraction_timestamp": row.get("extraction_timestamp") or row.get("extraction_timestamp_runner") or datetime.now(UTC).isoformat(),
        "race_id": row.get("race_id", ""),
        "race_date": row.get("race_date", ""),
        "racecourse": row.get("racecourse", ""),
        "race_no": row.get("race_no", ""),
        "runner_id": row.get("runner_id", ""),
        "horse_no": row.get("horse_no", ""),
        "horse_name": row.get("horse_name", ""),
        "horse_id_or_brand_no": row.get("horse_id_or_brand_no", ""),
        "abnormal_reason": f"blank_runner_id_quarantined_from_{table_name}",
        "raw_value": "|".join(str(row.get(key, "")) for key in row.keys()),
    }


def main() -> int:
    abnormal_path = PROCESSED / "abnormal_results.csv"
    abnormal_header, abnormal_rows = _read(abnormal_path)
    if not abnormal_header:
        abnormal_header = ABNORMAL_FIELDS

    removed_total = 0
    for name in NORMAL_TABLES:
        path = PROCESSED / name
        header, rows = _read(path)
        if not header:
            continue
        kept: list[dict[str, str]] = []
        removed: list[dict[str, str]] = []
        for row in rows:
            if "runner_id" in row and _blank(row.get("runner_id")):
                removed.append(row)
            else:
                kept.append(row)
        if removed:
            removed_total += len(removed)
            abnormal_rows.extend(_abnormal_from(name, row) for row in removed)
            _write(path, header, kept)

    # Preserve abnormal quarantine evidence while removing duplicate exact raw rows.
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, str]] = []
    for row in abnormal_rows:
        key = (row.get("race_id", ""), row.get("horse_name", ""), row.get("abnormal_reason", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    _write(abnormal_path, abnormal_header, deduped)

    print(f"quarantined_blank_runner_rows={removed_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
