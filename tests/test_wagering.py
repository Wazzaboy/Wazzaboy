import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hkjc_factory.probability import RunnerScore
from hkjc_factory.wagering.policy import BettingPolicy, select_overlay_bets
from hkjc_factory.wagering.staking import flat_stakes, fractional_kelly_stakes


class WageringTests(unittest.TestCase):
    def test_select_overlay_bets(self):
        scores = [
            RunnerScore("1", "H1", 0.3, 0.25, 0.28, 3.6, 4.2, 0.18, True),
            RunnerScore("2", "H2", 0.2, 0.22, 0.21, 4.7, 4.8, 0.01, False),
            RunnerScore("3", "H3", 0.15, 0.18, 0.17, 5.9, 7.5, 0.12, True),
        ]
        policy = BettingPolicy(overlay_threshold=0.03, max_bets_per_race=1, min_odds=2.0, max_odds=10.0)
        picks = select_overlay_bets(scores, policy)
        self.assertEqual(len(picks), 1)
        self.assertEqual(picks[0].runner_id, "1")

    def test_staking_plans(self):
        decision = [
            RunnerScore("1", "H1", 0.3, 0.25, 0.28, 3.6, 4.2, 0.18, True),
        ]
        policy = BettingPolicy()
        picks = select_overlay_bets(decision, policy)
        flat = flat_stakes(picks, unit=2.0)
        self.assertEqual(flat[0].stake, 2.0)

        kelly = fractional_kelly_stakes(picks, bankroll=1000.0, fraction=0.25, cap_per_bet=0.03)
        self.assertGreaterEqual(kelly[0].stake, 0)
        self.assertLessEqual(kelly[0].stake, 30.0)


if __name__ == "__main__":
    unittest.main()
