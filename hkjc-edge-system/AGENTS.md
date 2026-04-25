# Agent Instructions

## Scope
These instructions apply to the entire `hkjc-edge-system/` project tree.

## Conventions
- Keep parsing modules pure and testable (no direct network/file I/O inside parser functions).
- Centralize source definitions in `src/common/source_registry.py`.
- Write logs to CSV files in `logs/` through shared helpers in `src/common/logging_utils.py`.
- Validate schemas using helpers in `src/common/validation.py`.
- Add or update tests in `tests/` for any parser or leakage-rule change.

## Workflow
1. Run format/lint/tests before committing.
2. Keep changes incremental and documented in `README.md`.
