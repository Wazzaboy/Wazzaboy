import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import unittest

from hkjc_factory.probability import (
    blend_probabilities,
    implied_probabilities_from_odds,
    normalize_probabilities,
    score_race_board,
)


class ProbabilityTests(unittest.TestCase):
    def test_normalize_probabilities(self):
        values = normalize_probabilities([2, 3, 5])
        self.assertAlmostEqual(sum(values), 1.0)
        self.assertEqual(values, [0.2, 0.3, 0.5])

    def test_implied_probabilities(self):
        values = implied_probabilities_from_odds([2.0, 4.0])
        self.assertAlmostEqual(sum(values), 1.0)
        self.assertAlmostEqual(values[0], 2 / 3)
        self.assertAlmostEqual(values[1], 1 / 3)

    def test_blend_probabilities(self):
        model = [0.6, 0.4]
        market = [0.5, 0.5]
        blended = blend_probabilities(model, market, market_weight=0.5)
        self.assertAlmostEqual(blended[0], 0.55)
        self.assertAlmostEqual(blended[1], 0.45)

    def test_score_board_flags_overlay(self):
        scores = score_race_board(
            runner_ids=["1", "2"],
            horse_ids=["A", "B"],
            model_probabilities=[0.7, 0.3],
            current_odds=[2.5, 5.0],
            market_weight=0.5,
            overlay_threshold=0.02,
        )
        self.assertTrue(any(item.is_overlay for item in scores))


if __name__ == "__main__":
    unittest.main()
