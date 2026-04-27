"""CLI for walk-forward probability backtest summary."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .backtesting.runner import evaluate_probabilities


def main() -> None:
    parser = argparse.ArgumentParser(description="Run walk-forward backtest on probability rows")
    parser.add_argument("input", type=Path, help="JSON list of rows")
    parser.add_argument("--train-size", type=int, default=100)
    parser.add_argument("--test-size", type=int, default=50)
    parser.add_argument("--step", type=int, default=25)
    parser.add_argument("--market-weight", type=float, default=0.55)
    args = parser.parse_args()

    rows = json.loads(args.input.read_text())
    summary = evaluate_probabilities(
        rows,
        train_size=args.train_size,
        test_size=args.test_size,
        step=args.step,
        market_weight=args.market_weight,
    )

    print(json.dumps(asdict(summary), indent=2))


if __name__ == "__main__":
    main()
