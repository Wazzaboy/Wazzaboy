# Extraction Report

## Run Summary
- status: not_run
- note: starter template initialized

## Discovery Run
- source_registry_path: data/processed/hkjc/source_registry.csv
- validation_path: data/processed/hkjc/source_registry_validation.csv
- network_status: pending

## Missing-data gaps
- pending

## Parser errors
- pending

## Restricted pages
- pending

## Next task
- Implement first HKJC parser module (race card) with fixture-based tests.

## Discovery Run (2026-04-27T06:50:20.816138+00:00)
- validation_status: pass
- validation_issues: 0
- source_registry_sample:
- HKJC | Results | public | https://racing.hkjc.com/racing/information/English/Racing/LocalResults.aspx
- HKJC | Race Card | public | https://racing.hkjc.com/racing/information/English/racing/RaceCard.aspx
- HKJC | Current Odds | public | https://bet.hkjc.com/racing/pages/odds_wp.aspx
- HKJC | Dividends | error | https://racing.hkjc.com/racing/information/English/Racing/DividendsAll.aspx
- HKJC | Changes | public | https://racing.hkjc.com/racing/information/English/Racing/Changes.aspx

## HKJC Results Extraction Run (2026-04-27T06:57:17.688508+00:00)
- urls: 1
- races_rows: 1
- runners_rows: 14
- results_rows: 14
- dividends_rows: 10
- validation_status: pass
- validation_errors: 0
- missing_data_log: none
- parser_error_log: none

## HKJC Results Extraction Run (2026-04-27T07:02:34.606213+00:00)
- urls: 1
- races_rows: 1
- runners_rows: 14
- results_rows: 14
- dividends_rows: 13
- validation_status: pass
- validation_errors: 0
- missing_data_log: none
- parser_error_log: none

## Controlled Historical Backfill (2026-04-27T07:25:10.813827+00:00)
- total_races_processed: 81
- total_runner_rows: 1007
- total_result_rows: 1007
- total_dividend_rows: 1348
- total_comments_rows: 1007
- total_incident_rows: 81
- missing_data_rows: 1
- parser_failures: 0
- modeling_ready: no

## Controlled Historical Backfill (2026-04-27T07:55:32.115522+00:00)
- total_races_processed: 81
- total_runner_rows: 1007
- total_result_rows: 1007
- total_dividend_rows: 1348
- total_comments_rows: 1007
- total_incident_rows: 81
- missing_data_rows: 1
- parser_failures: 0
- modeling_ready: no
- requested_range: 2020-01-01 to 2026-04-27
- index_coverage_range: 2026-03-01 to 2026-03-29

## Discovery Run (2026-04-28T16:34:03.721504+00:00)
- validation_status: pass
- validation_issues: 0
- source_registry_sample:
- HKJC | Results | restricted | https://racing.hkjc.com/en-us/local/information/localresults
- HKJC | Race Card | restricted | https://racing.hkjc.com/en-us/local/information/racecard
- HKJC | Current Odds | restricted | https://bet.hkjc.com/racing/pages/odds_wp.aspx
- HKJC | Dividends | restricted | https://racing.hkjc.com/en-us/local/information/dividend
- HKJC | Changes | restricted | https://racing.hkjc.com/en-us/local/information/changes

## Validation Run (2026-04-28T16:36:14.876799+00:00)
- status: pass
- provenance_errors: 0
- leakage_issues: 0
- registry_validation: pass

## Extraction Report (2026-04-28T16:36:15.018377+00:00)
### Processed data row counts
- races: 81
- runners: 1007
- results: 1007
- dividends: 1348
- comments: 1007
- incidents: 81
- race_cards: 81
- changes: 81
- race_index: 81
- feature_store: 1007
### Log row counts
- missing_data: 1
- parser_errors: 0
- restricted_pages: 5
- conflicts: 0

## HKJC Results Extraction Run (2026-04-28T16:36:16.177597+00:00)
- urls: 1
- races_rows: 0
- runners_rows: 0
- results_rows: 0
- dividends_rows: 0
- validation_status: pass
- validation_errors: 0
- missing_data_log: none
- parser_error_log: none
