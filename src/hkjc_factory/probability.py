"""Probability, blending, and overlay decision logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


EPS = 1e-12


@dataclass(frozen=True)
class RunnerScore:
    runner_id: str
    horse_id: str
    model_probability: float
    market_probability: float
    blended_probability: float
    fair_odds: float
    current_odds: float
    expected_value: float
    is_overlay: bool


def normalize_probabilities(values: Iterable[float]) -> list[float]:
    items = list(values)
    if not items:
        raise ValueError("values must not be empty")
    if any(v < 0 for v in items):
        raise ValueError("probabilities must be non-negative")
    total = sum(items)
    if total <= EPS:
        raise ValueError("probability sum must be > 0")
    return [v / total for v in items]


def implied_probabilities_from_odds(decimal_odds: Iterable[float]) -> list[float]:
    odds = list(decimal_odds)
    if not odds:
        raise ValueError("odds must not be empty")
    raw = []
    for odd in odds:
        if odd <= 1.0:
            raise ValueError("decimal odds must be > 1.0")
        raw.append(1.0 / odd)
    return normalize_probabilities(raw)


def blend_probabilities(
    model_probabilities: Iterable[float],
    market_probabilities: Iterable[float],
    market_weight: float,
) -> list[float]:
    if not (0.0 <= market_weight <= 1.0):
        raise ValueError("market_weight must be in [0,1]")

    model = normalize_probabilities(model_probabilities)
    market = normalize_probabilities(market_probabilities)

    if len(model) != len(market):
        raise ValueError("model and market arrays must be same length")

    blended = [
        (1.0 - market_weight) * p_model + market_weight * p_market
        for p_model, p_market in zip(model, market)
    ]
    return normalize_probabilities(blended)


def score_race_board(
    runner_ids: list[str],
    horse_ids: list[str],
    model_probabilities: list[float],
    current_odds: list[float],
    market_weight: float,
    overlay_threshold: float,
) -> list[RunnerScore]:
    if len({len(runner_ids), len(horse_ids), len(model_probabilities), len(current_odds)}) != 1:
        raise ValueError("all runner arrays must have identical length")

    model_normalized = normalize_probabilities(model_probabilities)
    market_probabilities = implied_probabilities_from_odds(current_odds)
    blended = blend_probabilities(model_normalized, market_probabilities, market_weight)

    scores: list[RunnerScore] = []
    for idx in range(len(runner_ids)):
        p_blend = blended[idx]
        fair_odds = 1.0 / max(p_blend, EPS)
        ev = p_blend * current_odds[idx] - 1.0
        scores.append(
            RunnerScore(
                runner_id=runner_ids[idx],
                horse_id=horse_ids[idx],
                model_probability=model_normalized[idx],
                market_probability=market_probabilities[idx],
                blended_probability=p_blend,
                fair_odds=fair_odds,
                current_odds=current_odds[idx],
                expected_value=ev,
                is_overlay=ev >= overlay_threshold,
            )
        )

    return sorted(scores, key=lambda x: x.blended_probability, reverse=True)
