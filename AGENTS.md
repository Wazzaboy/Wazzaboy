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
- Every extracted row must include: `source_url`, `source_name`, `source_page_type`, `extraction_timestamp`.
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
### missing_data_log.csv columns
source_name, source_url, source_page_type, entity_type, entity_key, missing_field, reason, attempted_action, next_action, logged_at

### parser_error_log.csv columns
source_name, source_url, source_page_type, parser_module, error_type, error_message, failed_at, next_action

### restricted_pages_log.csv columns
source_name, source_url, source_page_type, restriction_type, access_status, reason, next_action, logged_at

### conflict_log.csv columns
entity_type, entity_key, field_name, hkjc_value, hkjc_source_url, secondary_source_name, secondary_value, secondary_source_url, severity, recommended_resolution, logged_at

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
A task is done only when Codex reports: files changed, commands run, tests run, outputs generated, row counts, validation status, missing-data gaps, parser errors, restricted pages, and next implementation step.
