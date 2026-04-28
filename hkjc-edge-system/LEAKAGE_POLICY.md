# HKJC Leakage Policy

## Timing classes

- `pre_race`: known before the race and usable for same-race prediction.
- `live_pre_race`: known before the race only if a timestamped snapshot proves availability before the decision time.
- `research_only`: usable for diagnostics, market-baseline research, or post-hoc benchmarking, but not as a same-race pre-race feature.
- `post_race_only`: published or known after the race; never usable for same-race prediction.
- `target`: label columns, not prediction features.

## Current repo rule

The current historical market odds are final/result-derived odds unless independently timestamped before the race. They are therefore `research_only`, not production-grade pre-race inputs.

## Blocked same-race features

The following are blocked from pre-race prediction for the same race:

- finish position
- beaten margin
- race time
- sectional time
- running position
- comments on running
- incident reports
- final dividends
- final/result-derived odds unless treated as `research_only`
- post-race veterinary findings

## Production betting prerequisites

A production bet signal requires:

- decision timestamp
- pre-race odds snapshot timestamp
- source URL
- model probability
- fair odds
- market odds
- expected value
- uncertainty haircut
- pass conditions
- staking method
- leakage audit pass
