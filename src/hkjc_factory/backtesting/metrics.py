"""Core probabilistic metrics for HKJC model evaluation."""

from __future__ import annotations

import math

EPS = 1e-12


def log_loss(y_true: list[int], y_prob: list[float]) -> float:
    if len(y_true) != len(y_prob) or not y_true:
        raise ValueError("y_true and y_prob must be same non-zero length")

    total = 0.0
    for y, p in zip(y_true, y_prob):
        p = min(max(float(p), EPS), 1.0 - EPS)
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / len(y_true)


def brier_score(y_true: list[int], y_prob: list[float]) -> float:
    if len(y_true) != len(y_prob) or not y_true:
        raise ValueError("y_true and y_prob must be same non-zero length")
    return sum((float(y) - float(p)) ** 2 for y, p in zip(y_true, y_prob)) / len(y_true)


def expected_calibration_error(y_true: list[int], y_prob: list[float], bins: int = 10) -> float:
    if len(y_true) != len(y_prob) or not y_true:
        raise ValueError("y_true and y_prob must be same non-zero length")
    if bins <= 0:
        raise ValueError("bins must be positive")

    bucket_counts = [0] * bins
    bucket_prob_sum = [0.0] * bins
    bucket_true_sum = [0.0] * bins

    for y, p in zip(y_true, y_prob):
        p = min(max(float(p), 0.0), 1.0)
        idx = min(int(p * bins), bins - 1)
        bucket_counts[idx] += 1
        bucket_prob_sum[idx] += p
        bucket_true_sum[idx] += float(y)

    n = len(y_true)
    ece = 0.0
    for c, p_sum, t_sum in zip(bucket_counts, bucket_prob_sum, bucket_true_sum):
        if c == 0:
            continue
        avg_p = p_sum / c
        avg_t = t_sum / c
        ece += (c / n) * abs(avg_p - avg_t)
    return ece
