# HKJC Edge Doctrine

This project is a source-verifiable HKJC quantitative racing scaffold. It is not a tip sheet and must not emit production betting advice unless the data, model, market, and staking gates pass.

## Valid edge sources

The model edge may only come from:

- better public data completeness
- cleaner historical joins
- timestamped odds capture
- leakage control
- calibration
- factor testing
- race selection
- expected-value discipline

## Invalid edge sources

The model edge must not come from:

- lucky-number thinking
- fake insider assumptions
- invented private data
- overfitted backtests
- same-race post-result leakage
- unverified horse, jockey, trainer, odds, veterinary, sectional, or race-card claims

## Source hierarchy

1. Official HKJC public sources are primary.
2. HKHorseDB or other third-party sources are secondary enrichment only, subject to access rights and explicit provenance.
3. Restricted, login-gated, paid, or copyrighted raw pages must not be archived or committed unless the repository has explicit rights to do so.

## Required provenance

Every normalized row must preserve enough provenance to trace it back to source material:

- `source_url`
- `source_name`
- `source_page_type`
- `extraction_timestamp`
- parser or script version where available

## Betting claim gate

No row may be interpreted as a production bet unless it has all of the following:

- fitted model probability
- fair odds
- timestamped market odds available before the race
- expected value
- uncertainty haircut
- staking rule
- leakage audit pass
- source provenance

Placeholder coefficients, final/result-derived odds, and scaffold outputs must force production staking to zero.

## Required status wording

Until the project has a production race-card parser, fitted/calibrated win and place models, and timestamped live odds history, the correct status is:

`structural_scaffold_only`

The repo must not claim `provisionally_ready`, `production_ready`, `profitable`, or `Benter-level` without a leakage-clean walk-forward market-blended backtest.