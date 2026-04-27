"""Leakage tagging rules for feature availability."""

from __future__ import annotations

POST_RACE_ONLY_FACTORS = {
    "same_race_results",
    "same_race_dividends",
    "same_race_comments_on_running",
    "same_race_incident_reports",
    "same_race_post_race_vet_notes",
}


def evaluate_factor(factor_name: str) -> dict[str, bool | str]:
    post_race_only = factor_name in POST_RACE_ONLY_FACTORS
    return {
        "factor_name": factor_name,
        "pre_race_usable": not post_race_only,
        "post_race_only": post_race_only,
        "leakage_risk": "high" if post_race_only else "low",
    }
