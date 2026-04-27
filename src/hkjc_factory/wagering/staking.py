"""Stake sizing helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .policy import BetDecision


@dataclass(frozen=True)
class StakePlan:
    runner_id: str
    stake: float


def flat_stakes(decisions: list[BetDecision], unit: float = 1.0) -> list[StakePlan]:
    if unit <= 0:
        raise ValueError("unit must be > 0")
    return [StakePlan(runner_id=d.runner_id, stake=unit) for d in decisions]


def fractional_kelly_stakes(
    decisions: list[BetDecision],
    bankroll: float,
    fraction: float = 0.25,
    cap_per_bet: float = 0.03,
) -> list[StakePlan]:
    if bankroll <= 0:
        raise ValueError("bankroll must be > 0")
    if not (0 < fraction <= 1):
        raise ValueError("fraction must be in (0,1]")
    if not (0 < cap_per_bet <= 1):
        raise ValueError("cap_per_bet must be in (0,1]")

    plans: list[StakePlan] = []
    for d in decisions:
        b = d.current_odds - 1.0
        p = 1.0 / d.fair_odds
        q = 1.0 - p
        raw_kelly = ((b * p) - q) / max(b, 1e-12)
        kelly = max(0.0, raw_kelly) * fraction
        kelly = min(kelly, cap_per_bet)
        plans.append(StakePlan(runner_id=d.runner_id, stake=bankroll * kelly))
    return plans
