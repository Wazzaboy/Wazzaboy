"""Normalization helpers preserving safe deterministic conversions."""

from __future__ import annotations

import re

_WS_RE = re.compile(r"\s+")


def normalize_whitespace(value: str) -> str:
    return _WS_RE.sub(" ", value).strip()


def to_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    value = normalize_whitespace(value)
    return int(value) if value else None


def to_float(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    value = normalize_whitespace(value).replace(",", "")
    return float(value) if value else None


def implied_probability_from_decimal_odds(decimal_odds: float) -> float:
    if decimal_odds <= 0:
        raise ValueError("decimal_odds must be positive")
    return 1.0 / decimal_odds
