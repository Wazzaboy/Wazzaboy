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
from .wagering.policy import BettingPolicy, select_overlay_bets
from .wagering.staking import flat_stakes, fractional_kelly_stakes


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


def run_with_policy(packet_path: Path, policy: BettingPolicy, bankroll: float = 0.0) -> dict:
    packet = load_packet(packet_path)
    scores = score_race_board(
        runner_ids=[r.runner_id for r in packet.runners],
        horse_ids=[r.horse_id for r in packet.runners],
        model_probabilities=[r.model_probability for r in packet.runners],
        current_odds=[r.current_win_odds for r in packet.runners],
        market_weight=policy.market_weight,
        overlay_threshold=policy.overlay_threshold,
    )

    decisions = select_overlay_bets(scores, policy)
    if bankroll > 0:
        stakes = fractional_kelly_stakes(decisions, bankroll=bankroll)
    else:
        stakes = flat_stakes(decisions, unit=1.0)

    return {
        "scores": [asdict(s) for s in scores],
        "decisions": [asdict(d) for d in decisions],
        "stakes": [asdict(s) for s in stakes],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="HKJC live board scorer")
    parser.add_argument("packet", type=Path, help="Path to race packet JSON")
    parser.add_argument("--market-weight", type=float, default=0.55)
    parser.add_argument("--overlay-threshold", type=float, default=0.03)
    parser.add_argument("--policy", type=Path, default=None, help="Optional betting policy JSON")
    parser.add_argument("--bankroll", type=float, default=0.0)
    args = parser.parse_args()

    if args.policy:
        payload = json.loads(args.policy.read_text())
        policy = BettingPolicy(
            market_weight=float(payload["market_weight"]),
            overlay_threshold=float(payload["overlay_threshold"]),
            max_bets_per_race=int(payload["max_bets_per_race"]),
            min_odds=float(payload["min_odds"]),
            max_odds=float(payload["max_odds"]),
        )
        result = run_with_policy(args.packet, policy=policy, bankroll=args.bankroll)
    else:
        result = run(args.packet, args.market_weight, args.overlay_threshold)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
