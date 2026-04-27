# HKHorseDB Enrichment Report

## Summary
- discovered_sources: 3
- restricted_sources: 2
- extraction_status: completed (secondary source only)

## What HKHorseDB adds beyond HKJC
- Potential secondary metadata and alternative tabular listings for horse/race/runner pages when publicly available.
- Cross-source validation signal for naming/metadata mismatches (no conflicts found in this controlled run).

## What is restricted
- Member/login pages were detected and marked as restricted.
- No access controls were bypassed; restricted pages were logged to `logs/restricted_pages_log.csv`.

## What conflicts with HKJC
- Conflict check completed.
- conflicts_logged: 0
- HKJC remains primary and no HKHorseDB values overwrite HKJC.

## Whether HKHorseDB is worth paying for
- Current public-access extraction yielded no parsed horses/races/runners rows.
- Value-for-money is currently **unproven** for this workflow without clearer public structured access and licensing clarity.

## What should be extracted next
1. Publicly accessible HKHorseDB tables with explicit horse identifiers and race-date keys.
2. Mapping keys to align HKHorseDB entities with HKJC `race_id` and `runner_id`.
3. Only after legal/terms review, evaluate paid access manually (no automation bypass).
