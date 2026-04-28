from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from src.common.source_registry import REQUIRED_SOURCE_FIELDS

VALID_ACCESS_STATUS = {
    "public",
    "restricted",
    "placeholder",
    "unknown",
    "network_unavailable",
    "error",
}


@dataclass(frozen=True)
class ValidationIssue:
    row_index: int
    field: str
    message: str


def validate_source_registry_rows(rows: Iterable[Mapping[str, str]]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for index, row in enumerate(rows):
        for field in REQUIRED_SOURCE_FIELDS:
            if not str(row.get(field, "")).strip():
                issues.append(
                    ValidationIssue(index, field, "required field is empty")
                )

        access_status = str(row.get("access_status", "")).strip()
        if access_status and access_status not in VALID_ACCESS_STATUS:
            issues.append(
                ValidationIssue(index, "access_status", f"invalid status: {access_status}")
            )

        source_name = str(row.get("source_name", "")).strip()
        model_value = str(row.get("model_value", "")).strip()
        if source_name == "HKHorseDB" and model_value != "secondary":
            issues.append(
                ValidationIssue(
                    index,
                    "model_value",
                    "HKHorseDB entries must be marked as secondary",
                )
            )

    return issues


def validation_summary(issues: list[ValidationIssue]) -> str:
    if not issues:
        return "pass"
    return f"fail ({len(issues)} issues)"
