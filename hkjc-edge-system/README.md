# HKJC Edge System

A scaffold for data extraction, normalization, feature engineering, and model experimentation for horse-racing edge analysis.

## Project layout
- `data/`: raw, processed, and fixture datasets.
- `src/`: source extraction/parsing, feature generation, and modeling modules.
- `scripts/`: runnable entrypoints for discovery, extraction, validation, and reporting.
- `logs/`: operational CSV logs.
- `reports/`: generated markdown reports.
- `tests/`: parser and validation test suites.

## Getting started
1. Copy `.env.example` to `.env` and set required values.
2. Install dependencies via `pip install -e .[dev]`.
3. Run tests via `pytest`.
