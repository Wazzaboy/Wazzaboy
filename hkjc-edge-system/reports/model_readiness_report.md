# Model Readiness Report

Generated at: 2026-04-28T16:33:56.678678+00:00

## Features available now
- race_id
- runner_id
- race_date
- racecourse
- race_no
- horse_no
- horse_name
- draw_num
- carried_weight_num
- handicap_rating_num
- jockey
- trainer
- market_odds
- market_implied_prob_raw
- pre_race_feature_set_version
- odds_quality_note
- source_url_runner
- source_name_runner
- source_page_type_runner
- extraction_timestamp_runner
- source_url_race
- source_name_race
- source_page_type_race
- extraction_timestamp_race

## Features blocked by missing data
- odds_snapshots.market_odds_timestamp (historical snapshot coverage missing)
- comments/incident/vet same-race fields blocked for pre-race prediction

## Leakage checks passed/failed
- status: passed
- blocked_post_race_feature_count: 0

## Backtest readiness
- status: provisionally_ready
- feature_store_rows: 1007
- missing_data_log_rows: 1
- parser_error_log_rows: 0
- time_split_train_rows: 568
- time_split_train_brier: 0.0679846004548941
- time_split_validation_rows: 214
- time_split_validation_brier: 0.0609894330460506
- time_split_test_rows: 225
- time_split_test_brier: 0.0631629285703012
- rolling_windows: 3
- rolling_avg_brier: 0.06432961990451477
- rolling_avg_log_loss: 0.23247988910285397

## Readiness thresholds
- min_split_rows: 200
- max_brier: 0.08
- max_log_loss: 0.26
- min_rolling_windows: 3
- thresholds_passed: true

## Minimum dataset requirements before serious modeling
- At least 2 full seasons of race-level coverage with stable schema.
- Reliable historical odds snapshot timestamps (pre-jump/near-jump).
- Complete pre-race horse, trainer, jockey history windows for recency features.
- Leakage audit pass across all candidate features.
- Explicit train/validation/test date split with no race-day cross-contamination.

## Notes
- Historical odds snapshots are incomplete; final odds are not equivalent to live bet-time odds.
- No betting picks are produced in this scaffold.
