"""Feature-store helpers for factor availability outputs."""

from __future__ import annotations

from src.features.leakage_tags import evaluate_factor


def build_factor_availability_rows(factor_names: list[str], source_name: str) -> list[dict[str, str | bool]]:
    rows: list[dict[str, str | bool]] = []
    for factor in factor_names:
        tags = evaluate_factor(factor)
        rows.append(
            {
                "factor_name": factor,
                "source_name": source_name,
                "source_section": "unknown",
                "source_url": "",
                "available": True,
                "pre_race_usable": tags["pre_race_usable"],
                "post_race_only": tags["post_race_only"],
                "leakage_risk": tags["leakage_risk"],
                "model_value": "pending",
                "extraction_priority": "medium",
            }
        )
    return rows
