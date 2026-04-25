from src.features.leakage_tags import evaluate_factor


def test_same_race_results_is_post_race_only() -> None:
    row = evaluate_factor("same_race_results")
    assert row["post_race_only"] is True
    assert row["pre_race_usable"] is False
    assert row["leakage_risk"] == "high"


def test_historical_form_is_prerace_usable() -> None:
    row = evaluate_factor("historical_form")
    assert row["post_race_only"] is False
    assert row["pre_race_usable"] is True
    assert row["leakage_risk"] == "low"
