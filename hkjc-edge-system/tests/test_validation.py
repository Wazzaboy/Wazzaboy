from __future__ import annotations

from src.common.validation import (
    ValidationIssue,
    validate_source_registry_rows,
    validation_summary,
)


def test_validate_source_registry_rows_detects_missing_required_field() -> None:
    rows = [
        {
            "source_url": "https://racing.hkjc.com/example",
            "source_name": "HKJC",
            "source_page_type": "Race Card",
            "access_status": "public",
            "model_value": "high",
            "leakage_risk": "low",
            "parser_difficulty": "",
            "notes": "sample",
        }
    ]

    issues = validate_source_registry_rows(rows)
    assert any(issue.field == "parser_difficulty" for issue in issues)


def test_validate_source_registry_rows_enforces_secondary_model_value() -> None:
    rows = [
        {
            "source_url": "https://www.hkhorsedb.com/",
            "source_name": "HKHorseDB",
            "source_page_type": "Secondary Enrichment",
            "access_status": "placeholder",
            "model_value": "high",
            "leakage_risk": "review_required",
            "parser_difficulty": "unknown",
            "notes": "secondary only",
        }
    ]

    issues = validate_source_registry_rows(rows)
    assert any("secondary" in issue.message for issue in issues)


def test_validation_summary_reports_pass_and_fail() -> None:
    assert validation_summary([]) == "pass"
    assert validation_summary([ValidationIssue(0, "source_url", "missing")]) == "fail (1 issues)"
