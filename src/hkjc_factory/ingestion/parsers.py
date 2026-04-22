"""Parsers from source payloads into canonical race packet structures."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .id_mapper import build_race_id, build_runner_id


REQUIRED_RACE_CARD_FIELDS = {
    "meeting_date",
    "venue",
    "race_number",
    "source_url",
    "source_timestamp_utc",
    "runners",
}

REQUIRED_RUNNER_FIELDS = {"horse_code", "saddle_number", "model_probability", "current_win_odds"}


def _assert_fields(payload: dict[str, Any], required: set[str], entity: str) -> None:
    missing = sorted(required.difference(payload.keys()))
    if missing:
        raise ValueError(f"{entity} missing required fields: {', '.join(missing)}")


def _validate_iso_utc(ts: str) -> None:
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("source_timestamp_utc must be valid ISO-8601") from exc

    if parsed.tzinfo is None:
        raise ValueError("source_timestamp_utc must include timezone")

    if parsed > datetime.now(timezone.utc):
        raise ValueError("source_timestamp_utc cannot be in the future")


def parse_race_card(payload: dict[str, Any]) -> dict[str, Any]:
    _assert_fields(payload, REQUIRED_RACE_CARD_FIELDS, "race_card")
    _validate_iso_utc(str(payload["source_timestamp_utc"]))

    race_id = build_race_id(
        meeting_date=str(payload["meeting_date"]),
        venue=str(payload["venue"]),
        race_number=int(payload["race_number"]),
    )

    runners_out = []
    for item in payload["runners"]:
        _assert_fields(item, REQUIRED_RUNNER_FIELDS, "runner")
        runner_id = build_runner_id(
            race_id=race_id,
            horse_code=str(item["horse_code"]),
            saddle_number=int(item["saddle_number"]),
        )
        runners_out.append(
            {
                "runner_id": runner_id,
                "horse_id": str(item["horse_code"]),
                "model_probability": float(item["model_probability"]),
                "current_win_odds": float(item["current_win_odds"]),
            }
        )

    return {
        "meeting_id": f"{payload['venue']}-{payload['meeting_date']}",
        "race_id": race_id,
        "source_url": str(payload["source_url"]),
        "source_timestamp_utc": str(payload["source_timestamp_utc"]),
        "runners": runners_out,
    }


def parse_odds_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    required = {"race_id", "source_timestamp_utc", "source_url", "odds"}
    _assert_fields(payload, required, "odds_snapshot")
    _validate_iso_utc(str(payload["source_timestamp_utc"]))

    odds_rows = []
    for row in payload["odds"]:
        if "runner_id" not in row or "current_win_odds" not in row:
            raise ValueError("odds row must include runner_id and current_win_odds")
        odd = float(row["current_win_odds"])
        if odd <= 1.0:
            raise ValueError("current_win_odds must be > 1.0")
        odds_rows.append({"runner_id": str(row["runner_id"]), "current_win_odds": odd})

    return {
        "race_id": str(payload["race_id"]),
        "source_url": str(payload["source_url"]),
        "source_timestamp_utc": str(payload["source_timestamp_utc"]),
        "odds": odds_rows,
    }
