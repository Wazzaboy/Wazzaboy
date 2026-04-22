import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hkjc_factory.backtesting.metrics import brier_score, expected_calibration_error, log_loss
from hkjc_factory.backtesting.runner import evaluate_probabilities
from hkjc_factory.backtesting.splits import walk_forward_splits


class BacktestingTests(unittest.TestCase):
    def test_walk_forward_splits(self):
        splits = walk_forward_splits(200, train_size=100, test_size=50, step=25)
        self.assertEqual(len(splits), 3)
        self.assertEqual(splits[0][0].start, 0)
        self.assertEqual(splits[0][1].start, 100)

    def test_metrics_bounds(self):
        y_true = [1, 0, 1, 0]
        y_prob = [0.8, 0.2, 0.7, 0.1]
        self.assertGreaterEqual(log_loss(y_true, y_prob), 0)
        self.assertGreaterEqual(brier_score(y_true, y_prob), 0)
        ece = expected_calibration_error(y_true, y_prob, bins=4)
        self.assertGreaterEqual(ece, 0)
        self.assertLessEqual(ece, 1)

    def test_evaluate_probabilities(self):
        rows = json.loads((ROOT / "tests/fixtures/backtest/probability_rows.json").read_text())
        summary = evaluate_probabilities(rows, train_size=120, test_size=60, step=40, market_weight=0.55)
        self.assertGreater(len(summary.folds), 0)
        self.assertGreaterEqual(summary.avg_model_log_loss, 0)
        self.assertGreaterEqual(summary.avg_market_log_loss, 0)
        self.assertGreaterEqual(summary.avg_blend_log_loss, 0)


if __name__ == "__main__":
    unittest.main()
