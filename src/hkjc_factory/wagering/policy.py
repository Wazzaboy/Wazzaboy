"""Overlay selection policy with explicit pass rules."""

from __future__ import annotations

from dataclasses import dataclass

from ..probability import RunnerScore


@dataclass(frozen=True)
class BettingPolicy:
    market_weight: float = 0.55
    overlay_threshold: float = 0.03
    max_bets_per_race: int = 2
    min_odds: float = 2.0
    max_odds: float = 30.0


@dataclass(frozen=True)
class BetDecision:
    runner_id: str
    horse_id: str
    current_odds: float
    fair_odds: float
    expected_value: float
    reason: str


def select_overlay_bets(scores: list[RunnerScore], policy: BettingPolicy) -> list[BetDecision]:
    candidates: list[BetDecision] = []

    for score in scores:
        if score.current_odds < policy.min_odds or score.current_odds > policy.max_odds:
            continue
        if score.expected_value < policy.overlay_threshold:
            continue

        candidates.append(
            BetDecision(
                runner_id=score.runner_id,
                horse_id=score.horse_id,
                current_odds=score.current_odds,
                fair_odds=score.fair_odds,
                expected_value=score.expected_value,
                reason="overlay_pass",
            )
        )

    candidates.sort(key=lambda x: x.expected_value, reverse=True)
    return candidates[: policy.max_bets_per_race]
