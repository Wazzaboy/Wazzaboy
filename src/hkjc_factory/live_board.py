"""Live board scoring CLI.

Input packet JSON format:
{
  "meeting_id": "...",
  "race_id": "...",
  "source_timestamp_utc": "2026-04-22T09:00:00Z",
  "runners": [
    {"runner_id": "1", "horse_id": "H1", "model_probability": 0.22, "current_win_odds": 4.8}
  ]
}
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .contracts import RacePacket, RunnerInput
from .probability import score_race_board


def load_packet(path: Path) -> RacePacket:
    payload = json.loads(path.read_text())
    runners = tuple(
        RunnerInput(
            runner_id=str(item["runner_id"]),
            horse_id=str(item["horse_id"]),
            model_probability=float(item["model_probability"]),
            current_win_odds=float(item["current_win_odds"]),
        )
        for item in payload["runners"]
    )

    packet = RacePacket(
        meeting_id=str(payload["meeting_id"]),
        race_id=str(payload["race_id"]),
        source_timestamp_utc=str(payload["source_timestamp_utc"]),
        runners=runners,
    )
    packet.validate()
    return packet


def run(packet_path: Path, market_weight: float, overlay_threshold: float) -> list[dict]:
    packet = load_packet(packet_path)

    scores = score_race_board(
        runner_ids=[r.runner_id for r in packet.runners],
        horse_ids=[r.horse_id for r in packet.runners],
        model_probabilities=[r.model_probability for r in packet.runners],
        current_odds=[r.current_win_odds for r in packet.runners],
        market_weight=market_weight,
        overlay_threshold=overlay_threshold,
    )
    return [asdict(score) for score in scores]


def main() -> None:
    parser = argparse.ArgumentParser(description="HKJC live board scorer")
    parser.add_argument("packet", type=Path, help="Path to race packet JSON")
    parser.add_argument("--market-weight", type=float, default=0.55)
    parser.add_argument("--overlay-threshold", type=float, default=0.03)
    args = parser.parse_args()

    result = run(args.packet, args.market_weight, args.overlay_threshold)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
