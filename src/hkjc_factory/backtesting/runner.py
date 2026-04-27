"""Simple walk-forward evaluator for model vs market vs blend."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics import brier_score, expected_calibration_error, log_loss
from .splits import walk_forward_splits


@dataclass(frozen=True)
class FoldMetrics:
    fold_index: int
    model_log_loss: float
    market_log_loss: float
    blend_log_loss: float
    model_brier: float
    market_brier: float
    blend_brier: float
    blend_ece: float


@dataclass(frozen=True)
class BacktestSummary:
    folds: tuple[FoldMetrics, ...]
    avg_model_log_loss: float
    avg_market_log_loss: float
    avg_blend_log_loss: float


def evaluate_probabilities(
    rows: list[dict],
    train_size: int = 100,
    test_size: int = 50,
    step: int = 25,
    market_weight: float = 0.55,
) -> BacktestSummary:
    """
    Expected row format (time sorted):
    {
      "won": 0|1,
      "model_probability": float,
      "market_probability": float
    }
    """
    if not rows:
        raise ValueError("rows cannot be empty")

    for row in rows:
        for key in ("won", "model_probability", "market_probability"):
            if key not in row:
                raise ValueError(f"row missing {key}")

    splits = walk_forward_splits(len(rows), train_size=train_size, test_size=test_size, step=step)
    if not splits:
        raise ValueError("no valid splits produced; adjust sizes")

    fold_metrics: list[FoldMetrics] = []
    for i, (_, test_slice) in enumerate(splits):
        test_rows = rows[test_slice]
        y_true = [int(r["won"]) for r in test_rows]
        p_model = [float(r["model_probability"]) for r in test_rows]
        p_market = [float(r["market_probability"]) for r in test_rows]
        p_blend = [
            min(max((1.0 - market_weight) * pm + market_weight * pk, 1e-12), 1.0 - 1e-12)
            for pm, pk in zip(p_model, p_market)
        ]

        fold_metrics.append(
            FoldMetrics(
                fold_index=i,
                model_log_loss=log_loss(y_true, p_model),
                market_log_loss=log_loss(y_true, p_market),
                blend_log_loss=log_loss(y_true, p_blend),
                model_brier=brier_score(y_true, p_model),
                market_brier=brier_score(y_true, p_market),
                blend_brier=brier_score(y_true, p_blend),
                blend_ece=expected_calibration_error(y_true, p_blend, bins=10),
            )
        )

    n = len(fold_metrics)
    return BacktestSummary(
        folds=tuple(fold_metrics),
        avg_model_log_loss=sum(f.model_log_loss for f in fold_metrics) / n,
        avg_market_log_loss=sum(f.market_log_loss for f in fold_metrics) / n,
        avg_blend_log_loss=sum(f.blend_log_loss for f in fold_metrics) / n,
    )
