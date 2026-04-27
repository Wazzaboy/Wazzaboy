"""Validation helpers for processed schema completeness."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from src.common.source_registry import DISCOVERY_REQUIRED_FIELDS

REQUIRED_SCHEMAS: dict[str, list[str]] = {
    "source_discovery": DISCOVERY_REQUIRED_FIELDS,
    "races": [
        "source_url",
        "source_name",
        "extraction_timestamp",
        "race_id",
        "meeting_id",
        "race_date",
        "racecourse",
        "race_no",
        "race_name",
        "class",
        "rating_band",
        "distance",
        "surface",
        "course",
        "going",
        "prize_money",
        "field_size",
    ],
    "runners": [
        "source_url",
        "source_name",
        "extraction_timestamp",
        "runner_id",
        "race_id",
        "race_date",
        "racecourse",
        "race_no",
        "horse_no",
        "horse_name",
        "horse_id_or_brand_no",
        "draw",
        "jockey",
        "trainer",
        "carried_weight",
        "handicap_rating",
        "rating_change",
        "declared_body_weight",
        "body_weight_change",
        "gear",
        "gear_change",
        "odds",
        "finish_position",
        "beaten_margin",
        "race_time",
        "sectional_time",
        "running_position",
        "comments_or_notes",
    ],
    "dividends": [
        "source_url",
        "source_name",
        "extraction_timestamp",
        "race_id",
        "pool_type",
        "winning_combination",
        "dividend",
        "raw_value",
    ],
    "odds_snapshots": [
        "source_url",
        "source_name",
        "extraction_timestamp",
        "race_id",
        "runner_id",
        "race_date",
        "racecourse",
        "race_no",
        "horse_name",
        "odds_type",
        "odds_value",
        "odds_timestamp",
        "snapshot_stage",
        "raw_value",
    ],
    "factor_availability": [
        "factor_name",
        "source_name",
        "source_section",
        "source_url",
        "available",
        "pre_race_usable",
        "post_race_only",
        "leakage_risk",
        "model_value",
        "extraction_priority",
    ],
}


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    missing_columns: tuple[str, ...]


def validate_columns(columns: Iterable[str], required: Iterable[str]) -> ValidationResult:
    have = set(columns)
    missing = tuple(col for col in required if col not in have)
    return ValidationResult(valid=not missing, missing_columns=missing)


def validate_records(table_name: str, rows: Iterable[Mapping[str, str]]) -> ValidationResult:
    required = REQUIRED_SCHEMAS[table_name]
    first = next(iter(rows), None)
    if first is None:
        return ValidationResult(valid=False, missing_columns=tuple(required))
    return validate_columns(first.keys(), required)


def validate_csv_file(table_name: str, path: Path) -> ValidationResult:
    required = REQUIRED_SCHEMAS[table_name]
    if not path.exists():
        return ValidationResult(valid=False, missing_columns=tuple(required))
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
    return validate_columns(fieldnames, required)
