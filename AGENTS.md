# HKJC Edge System — Codex Instructions

## Role

Act as a senior Python data engineer, HKJC racing-data extraction engineer, quantitative racing-model engineer, and no-hallucination auditor.

## Mission

Build a source-verifiable HKJC-first racing-data pipeline and modeling foundation.

The system must:
- collect official HKJC public data first
- use HKHorseDB only as secondary enrichment/cross-check data
- preserve raw source files where permitted
- parse structured tables
- validate extracted data
- log missing data
- log restricted pages
- log parser errors
- log HKJC vs secondary-source conflicts
- create model-ready factor tables only after leakage checks

## Source priority

1. HKJC official public sources:
   - racing.hkjc.com
   - bet.hkjc.com
   - hkjc.com

2. HKHorseDB:
   - secondary enrichment only
   - never overrides HKJC official data unless manually reviewed

3. Other public sources:
   - optional only
   - must be source-logged
   - must be clearly labeled as third-party

## Non-negotiable rules

- Do not hallucinate.
- Do not invent HKJC data.
- Do not hardcode fake horse, race, odds, result, dividend, trainer, jockey, veterinary, sectional, or incident records.
- Do not bypass login, membership, paywalls, captcha, bot protection, access controls, or private betting/account pages.
- Respect rate limits, robots.txt, copyright, and site terms.
- Every extracted row must include:
  - source_url
  - source_name
  - source_page_type
  - extraction_timestamp
- Preserve raw values before normalization.
- Missing fields must be logged, not guessed.
- Parser failures must be logged, not silently ignored.
- Restricted pages must be logged, not bypassed.
- HKJC official data is the primary truth source.
- HKHorseDB is secondary enrichment/cross-check data.
- If HKJC and HKHorseDB conflict, keep both and write to conflict_log.
- Post-race data must be tagged as post_race_only.
- Same-race post-race data must never be used as pre-race prediction data.

## Required data layers

1. Raw archive
2. Parsed staging tables
3. Normalized database-ready tables
4. Feature store
5. Model probability outputs
6. Betting/EV simulation outputs
7. Reports and logs

## Required output folders

- data/raw/hkjc/
- data/raw/hkhorsedb/
- data/processed/hkjc/
- data/processed/hkhorsedb/
- data/fixtures/
- logs/
- reports/
- tests/

## Required logs

### missing_data_log.csv
Columns:
- source_name
- source_url
- source_page_type
- entity_type
- entity_key
- missing_field
- reason
- attempted_action
- next_action
- logged_at

### parser_error_log.csv
Columns:
- source_name
- source_url
- source_page_type
- parser_module
- error_type
- error_message
- failed_at
- next_action

### restricted_pages_log.csv
Columns:
- source_name
- source_url
- source_page_type
- restriction_type
- access_status
- reason
- next_action
- logged_at

### conflict_log.csv
Columns:
- entity_type
- entity_key
- field_name
- hkjc_value
- hkjc_source_url
- secondary_source_name
- secondary_value
- secondary_source_url
- severity
- recommended_resolution
- logged_at

## Required HKJC page groups

Map and extract where publicly accessible:
- Race Card
- Current Odds
- Results
- Dividends
- Changes
- Trainers’ Entries
- Jockeys’ Rides
- Comments on Running
- Racing Incident Report
- Race Report
- Veterinary Records
- Health Record
- Barrier Trial Results
- Trackwork
- Past Incidents Extract
- Form Line Report
- Exceptional Factors
- Horses
- Jockeys
- Trainers
- Jockeys & Trainers
- Rating List
- Draw Statistics
- Fixtures
- SpeedPRO / sectional / running-position data if publicly accessible

## Required schemas

Every processed file must include source fields.

### races.csv
- source_url
- source_name
- extraction_timestamp
- race_id
- meeting_id
- race_date
- racecourse
- race_no
- race_name
- class
- rating_band
- distance
- surface
- course
- going
- prize_money
- field_size

### runners.csv
- source_url
- source_name
- extraction_timestamp
- runner_id
- race_id
- race_date
- racecourse
- race_no
- horse_no
- horse_name
- horse_id_or_brand_no
- draw
- jockey
- trainer
- carried_weight
- handicap_rating
- rating_change
- declared_body_weight
- body_weight_change
- gear
- gear_change
- odds
- finish_position
- beaten_margin
- race_time
- sectional_time
- running_position
- comments_or_notes

### dividends.csv
- source_url
- source_name
- extraction_timestamp
- race_id
- pool_type
- winning_combination
- dividend
- raw_value

### odds_snapshots.csv
- source_url
- source_name
- extraction_timestamp
- race_id
- runner_id
- race_date
- racecourse
- race_no
- horse_name
- odds_type
- odds_value
- odds_timestamp
- snapshot_stage
- raw_value

### factor_availability.csv
- factor_name
- source_name
- source_section
- source_url
- available
- pre_race_usable
- post_race_only
- leakage_risk
- model_value
- extraction_priority

## Modeling rules

Initial model stack:
1. fundamental probability model
2. market implied probability model
3. Benter-style market blend
4. calibration layer
5. expected-value layer
6. fractional Kelly staking simulator

Required formulas:
- implied probability from odds
- overround normalization
- softmax / multinomial logit probability
- fundamental score
- market blend
- calibration correction
- expected value
- edge
- uncertainty haircut
- fractional Kelly
- recency-weighted form
- class-change adjustment
- draw-bias adjustment
- jockey/trainer shrinkage

## Leakage rules

- Same-race results cannot be pre-race features.
- Same-race dividends cannot be pre-race features.
- Same-race comments on running cannot be pre-race features.
- Same-race incident reports cannot be pre-race features.
- Same-race post-race veterinary notes cannot be pre-race features.
- Final odds must be clearly tagged by timestamp.
- Historical post-race data can only become a feature for future races.

## Engineering standards

- Use Python.
- Prefer `httpx` or `requests` for static pages.
- Use `BeautifulSoup` or `lxml` for HTML parsing.
- Use Playwright only for public pages that require rendering.
- Use pandas or polars for tabular exports.
- Use pytest for parser and validation tests.
- Keep functions typed where practical.
- Write deterministic parsers.
- Do not silently drop failed rows.
- Do not overwrite raw files.
- Use respectful rate limits.
- Store raw files with content hashes.

## Done criteria

A task is done only when Codex reports:
1. files created or changed
2. commands run
3. tests run
4. outputs generated
5. row counts
6. validation status
7. missing-data gaps
8. parser errors
9. restricted pages
10. next implementation step

Do not stop at planning when implementation is possible.
