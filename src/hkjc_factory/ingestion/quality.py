"""Data quality checks for ingestion outputs."""

from __future__ import annotations

from datetime import datetime, timezone


def check_snapshot_freshness_seconds(source_timestamp_utc: str, max_age_seconds: int) -> bool:
    ts = datetime.fromisoformat(source_timestamp_utc.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        raise ValueError("source_timestamp_utc must include timezone")
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    return age <= max_age_seconds


def check_packet_completeness(packet: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not packet.get("meeting_id"):
        errors.append("meeting_id missing")
    if not packet.get("race_id"):
        errors.append("race_id missing")

    runners = packet.get("runners", [])
    if not runners:
        errors.append("runners empty")
    else:
        for i, runner in enumerate(runners):
            for field in ("runner_id", "horse_id", "model_probability", "current_win_odds"):
                if field not in runner:
                    errors.append(f"runner[{i}] missing {field}")

    return (len(errors) == 0, errors)
