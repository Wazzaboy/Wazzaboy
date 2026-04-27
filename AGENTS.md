# AGENTS.md — HKJC Quant Factory

## Operating intent
Use Codex as a disciplined engineering team. Do **not** use LLM free-form handicapping as the final probability source.

## Non-negotiable rules
1. Never invent race data or fields.
2. Use official HKJC source pages as canonical unless explicitly configured otherwise.
3. Missing stays missing; never infer missing odds or outcomes.
4. Any parser change requires fixture updates and regression tests.
5. Any feature change requires leakage checks.
6. Any model report must include calibration and market-only comparisons.
7. Do not optimize on ROI alone.

## Agent roles
### 1) Data Engineer Agent
- Build/maintain ingestion pipelines.
- Enforce canonical schemas.
- Maintain ID mapping and deduplication.
- Monitor freshness and completeness.

### 2) Feature Engineer Agent
- Build versioned feature modules.
- Enforce event-time correctness.
- Add leakage assertions for each feature family.

### 3) Model Research Agent
- Train benchmark models.
- Run time-based validation.
- Produce reproducible experiment artifacts.

### 4) Betting Scientist Agent
- Calibrate probabilities.
- Blend with market implied probabilities.
- Simulate overlays, stake rules, and pass logic.

### 5) QA/Audit Agent
- Validate schema compatibility.
- Detect stale odds, impossible values, broken joins.
- Block promotions when gates fail.

## Promotion gates
A candidate is not deployable unless all are true:
- Beats market-only baseline on out-of-sample probability quality.
- Shows acceptable calibration error.
- Passes leakage audit.
- Passes reproducibility check from clean state.
- Produces race-day inference artifact with traceable inputs.
