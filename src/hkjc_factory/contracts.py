"""Deterministic data contracts for race-day packets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class RunnerInput:
    runner_id: str
    horse_id: str
    model_probability: float
    current_win_odds: float

    def validate(self) -> None:
        if not self.runner_id or not self.horse_id:
            raise ValueError("runner_id and horse_id are required")
        if not (0.0 <= self.model_probability <= 1.0):
            raise ValueError("model_probability must be in [0,1]")
        if self.current_win_odds <= 1.0:
            raise ValueError("current_win_odds must be > 1.0")


@dataclass(frozen=True)
class RacePacket:
    meeting_id: str
    race_id: str
    source_timestamp_utc: str
    runners: tuple[RunnerInput, ...]

    def validate(self) -> None:
        if not self.meeting_id or not self.race_id:
            raise ValueError("meeting_id and race_id are required")
        if not self.runners:
            raise ValueError("runners must not be empty")

        seen_runner_ids: set[str] = set()
        for runner in self.runners:
            runner.validate()
            if runner.runner_id in seen_runner_ids:
                raise ValueError(f"duplicate runner_id: {runner.runner_id}")
            seen_runner_ids.add(runner.runner_id)

        try:
            ts = datetime.fromisoformat(self.source_timestamp_utc.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("source_timestamp_utc must be ISO-8601") from exc

        if ts.tzinfo is None:
            raise ValueError("source_timestamp_utc must include timezone")

        now_utc = datetime.now(timezone.utc)
        if ts > now_utc:
            raise ValueError("source_timestamp_utc cannot be in the future")
