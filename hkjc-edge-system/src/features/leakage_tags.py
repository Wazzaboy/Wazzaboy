from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

PRE_RACE = "pre_race"
LIVE_PRE_RACE = "live_pre_race"
RESEARCH_ONLY = "research_only"
POST_RACE_ONLY = "post_race_only"
TARGET = "target"

_TARGET_FIELDS = {"target_win", "target_place"}
_RESEARCH_ONLY_FIELDS = {
    "market_odds",
    "market_implied_prob_raw",
    "odds_quality_note",
}
_POST_RACE_FIELDS = {
    "finish_position",
    "beaten_margin",
    "race_time",
    "sectional_time",
    "running_position",
    "comments_or_notes",
    "incident_report_available",
    "dividend",
    "results",
    "win_odds",
}


@dataclass(frozen=True)
class LeakageIssue:
    feature_name: str
    reason: str


def classify_feature(feature_name: str) -> str:
    name = feature_name.lower().strip()
    if name in _TARGET_FIELDS or name.startswith("target_"):
        return TARGET

    if name in _POST_RACE_FIELDS:
        return POST_RACE_ONLY

    if name in _RESEARCH_ONLY_FIELDS:
        return RESEARCH_ONLY

    return PRE_RACE


def build_feature_tags(feature_names: Iterable[str]) -> dict[str, str]:
    return {name: classify_feature(name) for name in feature_names}


def find_leakage_features(feature_names: Iterable[str]) -> list[LeakageIssue]:
    issues: list[LeakageIssue] = []
    for name in feature_names:
        tag = classify_feature(name)
        if tag == POST_RACE_ONLY:
            issues.append(
                LeakageIssue(
                    feature_name=name,
                    reason="post_race feature cannot be used for same-race prediction",
                )
            )
    return issues


def validate_feature_set(feature_names: Iterable[str]) -> tuple[bool, list[LeakageIssue]]:
    issues = find_leakage_features(feature_names)
    return len(issues) == 0, issues
