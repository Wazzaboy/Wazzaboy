# HKJC Codex Operating System

## 1) Repository architecture

```text
hkjc-quant/
  configs/
  data_contracts/
  ingestion/
  storage/
  features/
  modeling/
  backtesting/
  live/
  qa/
  tests/
  reports/
```

Design goals:
- deterministic ingestion
- explicit contracts
- feature versioning
- reproducible experiments
- transparent race-day inference

## 2) Canonical data model

Minimum entities:
- races
- runners
- horses
- odds_snapshots
- results
- dividends
- draw_stats
- trackwork
- barrier_trials
- vet_records
- comments_running
- race_reports
- trainer_stats
- jockey_stats

Key fields in every table:
- source_name
- source_url
- source_timestamp_utc
- ingested_at_utc
- schema_version

Identity conventions:
- meeting_id
- race_id
- runner_id
- horse_id

## 3) Ingestion pipeline (priority build)

Priority sequence:
1. race card parser
2. odds snapshot collector
3. results/dividends parser
4. trackwork parser
5. barrier trial parser
6. vet record parser
7. comments/race report parser

Each parser must provide:
- deterministic output schema
- fixture-backed tests
- parser drift alarms
- idempotent re-run behavior

## 4) Feature store specification

Feature families:
- ability_class
- suitability
- pace_trip
- readiness
- connections
- market
- race_structure
- text_signals

Every feature requires metadata:
- owner
- definition
- source tables
- lookback
- null treatment
- leakage assertion
- version

## 5) Baseline model stack

Required baselines:
1. market-only implied probability model
2. conditional logit model
3. gradient boosting model
4. blended model (market + best fundamental)

Recommended calibration:
- isotonic
- platt
- beta calibration

Selection criterion:
- out-of-sample log loss first
- calibration second
- ROI stability third

## 6) Market blending layer

Target: exploit incremental edge over public market.

Blend templates:
- convex blend: p = w * p_model + (1-w) * p_market
- logistic stack with regularization
- late-odds adjustment term

Constraints:
- probabilities sum to one at race level
- no negative overlay execution

## 7) Backtest protocol

Use walk-forward time splits only.

Mandatory outputs:
- log loss
- Brier score
- calibration curve / ECE
- top-1 and top-3 hit rates
- ROI overall
- ROI by odds bucket
- ROI by venue/surface/class/distance
- turnover, strike rate, drawdown proxy
- market-only benchmark deltas

## 8) Race-day workflow

Phases:
1. Early card packet build
2. Morning data refresh
3. Pre-race odds/changes refresh
4. Final fair-odds + overlay decision

Every probability update must be attributable to changed inputs.

## 9) QA and monitoring

Continuous checks:
- schema drift
- stale feed detection
- duplicate runner detection
- impossible-value checks
- feature leakage scans
- calibration drift

Retrain triggers:
- sustained log-loss degradation
- calibration drift above threshold
- market-blend underperformance

## 10) Hard safety policy

Never:
- infer missing odds
- silently change feature definitions
- promote a model on ROI slice alone
- bypass regression tests
- deploy without reproducibility logs

Always:
- attach provenance
- keep deterministic transforms
- produce reviewable diffs and reports
