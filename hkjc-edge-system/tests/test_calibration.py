from __future__ import annotations

import pandas as pd

from src.models.calibration import calibrate_probability, fit_calibration_from_historical_folds, fit_logistic_calibration


def test_calibrate_probability_bounds() -> None:
    value = calibrate_probability(0.0, slope=1.0, intercept=0.0)
    assert 0.0 < value < 1.0


def test_fit_logistic_calibration_returns_non_identity_on_signal() -> None:
    probabilities = [0.2, 0.3, 0.7, 0.8]
    targets = [0, 0, 1, 1]
    slope, intercept = fit_logistic_calibration(probabilities, targets, epochs=200, learning_rate=0.1)
    assert slope > 0.5
    assert abs(intercept) < 2.0


def test_fit_calibration_from_historical_folds_returns_params() -> None:
    df = pd.DataFrame(
        [
            {"race_date": "2026-01-01", "blended_prob": 0.20, "target_win": 0},
            {"race_date": "2026-01-02", "blended_prob": 0.30, "target_win": 0},
            {"race_date": "2026-01-03", "blended_prob": 0.35, "target_win": 0},
            {"race_date": "2026-01-04", "blended_prob": 0.45, "target_win": 1},
            {"race_date": "2026-01-05", "blended_prob": 0.55, "target_win": 1},
            {"race_date": "2026-01-06", "blended_prob": 0.65, "target_win": 1},
            {"race_date": "2026-01-07", "blended_prob": 0.70, "target_win": 1},
        ]
    )
    slope, intercept = fit_calibration_from_historical_folds(df, min_train_dates=3)
    assert slope > 0
    assert -5 < intercept < 5
