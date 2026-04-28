from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class RollingWindow:
    window_id: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    train_dates: tuple[str, ...]
    test_dates: tuple[str, ...]


def build_rolling_origin_windows(
    unique_dates: Sequence[str],
    *,
    initial_train_size: int = 30,
    step_size: int = 7,
    test_size: int = 7,
) -> list[RollingWindow]:
    if initial_train_size < 1 or step_size < 1 or test_size < 1:
        raise ValueError("window sizes must be positive")

    dates = list(unique_dates)
    windows: list[RollingWindow] = []
    train_end_idx = initial_train_size
    window_id = 1
    while (train_end_idx + test_size) <= len(dates):
        train_dates = tuple(dates[:train_end_idx])
        test_dates = tuple(dates[train_end_idx : train_end_idx + test_size])
        windows.append(
            RollingWindow(
                window_id=window_id,
                train_start=train_dates[0],
                train_end=train_dates[-1],
                test_start=test_dates[0],
                test_end=test_dates[-1],
                train_dates=train_dates,
                test_dates=test_dates,
            )
        )
        train_end_idx += step_size
        window_id += 1

    return windows


def brier_score(probabilities: list[float], targets: list[int]) -> float:
    if len(probabilities) != len(targets):
        raise ValueError("probabilities and targets length mismatch")
    if not probabilities:
        return float("nan")
    return sum((p - y) ** 2 for p, y in zip(probabilities, targets, strict=True)) / len(probabilities)


def log_loss(probabilities: list[float], targets: list[int], epsilon: float = 1e-6) -> float:
    if len(probabilities) != len(targets):
        raise ValueError("probabilities and targets length mismatch")
    if not probabilities:
        return float("nan")

    clipped = [min(max(float(p), epsilon), 1.0 - epsilon) for p in probabilities]
    total = 0.0
    for p, y in zip(clipped, targets, strict=True):
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / len(clipped)
