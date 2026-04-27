from __future__ import annotations

from src.models.backtest import build_rolling_origin_windows, brier_score, log_loss


def test_build_rolling_origin_windows_orders_dates() -> None:
    dates = [f"2026-01-{day:02d}" for day in range(1, 16)]
    windows = build_rolling_origin_windows(dates, initial_train_size=7, step_size=3, test_size=3)
    assert len(windows) == 2
    assert windows[0].train_end == "2026-01-07"
    assert windows[0].test_start == "2026-01-08"
    assert windows[1].train_end == "2026-01-10"


def test_brier_and_log_loss_return_positive_values() -> None:
    probabilities = [0.1, 0.8, 0.7, 0.2]
    targets = [0, 1, 1, 0]
    assert 0 <= brier_score(probabilities, targets) < 1
    assert 0 <= log_loss(probabilities, targets) < 1
