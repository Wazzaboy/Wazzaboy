import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import unittest

from hkjc_factory.live_board import run, run_with_policy
from hkjc_factory.wagering.policy import BettingPolicy


class LiveBoardTests(unittest.TestCase):
    def test_run_returns_ranked_scores(self):
        packet = Path("configs/sample_race_packet.json")
        output = run(packet, market_weight=0.55, overlay_threshold=0.03)
        self.assertGreater(len(output), 0)
        self.assertIn("blended_probability", output[0])
        self.assertIn("expected_value", output[0])
        self.assertGreaterEqual(output[0]["blended_probability"], output[-1]["blended_probability"])

    def test_run_with_policy(self):
        packet = Path("configs/sample_race_packet.json")
        policy = BettingPolicy(
            market_weight=0.55,
            overlay_threshold=0.15,
            max_bets_per_race=2,
            min_odds=2.0,
            max_odds=12.0,
        )
        output = run_with_policy(packet, policy=policy, bankroll=1000.0)
        self.assertIn("scores", output)
        self.assertIn("decisions", output)
        self.assertIn("stakes", output)
        self.assertLessEqual(len(output["decisions"]), 2)


if __name__ == "__main__":
    unittest.main()
