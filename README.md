# HKJC Quant Modeling Factory (Codex-Operated)

This repository defines a **no-hallucination, market-blended probabilistic modeling system** for HKJC race analysis.

## Mission
Build a production-grade pipeline where:
- official HKJC data is the source of truth,
- calibrated statistical/ML models produce probabilities,
- market odds are blended into final estimates,
- wagering decisions are generated only when overlays pass strict gates.

Codex is used as an engineering/research operator for ingestion, testing, feature generation, model evaluation, and auditability.

## Core Principles
1. **Data integrity first** (never invent data).
2. **Probabilities, not picks**.
3. **Calibration beats storytelling**.
4. **Market blend required**.
5. **Pass often; bet only overlays**.
6. **Every change must be testable and reviewable**.

## Start Here
- [`HKJC_Codex_OS.md`](HKJC_Codex_OS.md): full operating blueprint.
- [`AGENTS.md`](AGENTS.md): role instructions and non-negotiable quality gates.
- [`TASKS.md`](TASKS.md): staged implementation plan.

## Status
This is the initial system design baseline. Implementation should proceed in staged milestones with regression-safe increments.
