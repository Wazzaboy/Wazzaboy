from __future__ import annotations

from src.features.leakage_tags import POST_RACE_ONLY, PRE_RACE, TARGET, classify_feature, validate_feature_set


def test_classify_feature_tags() -> None:
    assert classify_feature("draw_num") == PRE_RACE
    assert classify_feature("finish_position") == POST_RACE_ONLY
    assert classify_feature("target_win") == TARGET


def test_validate_feature_set_blocks_post_race_fields() -> None:
    ok, issues = validate_feature_set(["draw_num", "handicap_rating_num", "comments_or_notes"])
    assert not ok
    assert len(issues) == 1
    assert issues[0].feature_name == "comments_or_notes"
