# HKJC Quant Factory Implementation Tasks

## Milestone 0 — Foundation
- [x] Create directory skeleton and package structure.
- [x] Add schema contract files for core entities.
- [ ] Add CI checks for formatting, tests, and schema validation.

## Milestone 1 — Deterministic ingestion
- [ ] Implement race card parser with fixtures.
- [ ] Implement odds snapshot collector with scheduling.
- [ ] Implement results/dividends parser.
- [x] Implement ID mapping service for meeting/race/horse/runner.
- [x] Add freshness and completeness monitors.

## Milestone 2 — Feature store v1
- [ ] Implement ability/class features.
- [ ] Implement suitability and draw interaction features.
- [ ] Implement pace/trip and readiness features.
- [ ] Implement market and race-structure features.
- [ ] Add feature-level leakage tests.

## Milestone 3 — Modeling benchmarks
- [ ] Train market-only baseline.
- [ ] Train conditional logit baseline.
- [ ] Train GBDT baseline.
- [ ] Add calibration candidates (isotonic/Platt/beta).
- [ ] Implement blend experiments.

## Milestone 4 — Backtest and decision policy
- [x] Build walk-forward backtest harness.
- [x] Report all mandatory metrics and segment breakdowns.
- [ ] Implement overlay thresholding and pass rules.
- [ ] Simulate stake sizing and risk controls.

## Milestone 5 — Live race-day engine
- [ ] Build race packet generation service.
- [ ] Implement pre-race refresh and final decision tick.
- [ ] Add auditable decision logs.
- [ ] Add drift monitoring and retrain trigger alerts.

## Definition of done (global)
A stage is complete only if:
- [ ] tests pass,
- [ ] leakage checks pass,
- [ ] reproducibility report generated,
- [ ] market-only comparison included,
- [ ] calibration report included,
- [ ] QA sign-off artifact produced.
