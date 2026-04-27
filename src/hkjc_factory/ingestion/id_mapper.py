"""Canonical ID builders for deterministic mapping."""

from __future__ import annotations

import hashlib


def _hash_token(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def build_race_id(meeting_date: str, venue: str, race_number: int) -> str:
    token = f"{meeting_date}|{venue.strip().upper()}|R{int(race_number)}"
    return f"RACE-{_hash_token(token)}"


def build_runner_id(race_id: str, horse_code: str, saddle_number: int) -> str:
    token = f"{race_id}|{horse_code.strip().upper()}|N{int(saddle_number)}"
    return f"RUN-{_hash_token(token)}"
