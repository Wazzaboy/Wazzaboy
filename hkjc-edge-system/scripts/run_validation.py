#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.validation import validate_source_registry_rows, validation_summary
from src.features.leakage_tags import POST_RACE_ONLY, RESEARCH_ONLY, build_feature_tags

PROVENANCE_FIELDS = ["source_url", "source_name", "source_page_type", "extraction_timestamp"]
GOVERNANCE_FILES = ["EDGE_DOCTRINE.md", "LEAKAGE_POLICY.md", "SOURCE_REGISTRY.yaml"]
SCAFFOLD_REQUIRED = {
    "fundamental_model_status": "scaffold_only",
    "fundamental_coefficient_source": "placeholder_not_fitted",
    "blend_model_status": "scaffold_only",
    "blend_weight_source": "fixed_placeholder_not_fitted",
    "bet_signal_status": "blocked_scaffold_only",
    "stake_permission": "not_allowed_placeholder_model",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle), [])


def blank(value: object) -> bool:
    return str(value if value is not None else "").strip() in {"", "NULL", "nan", "NaN"}


def check_provenance(rows: list[dict[str, str]], table: str) -> list[str]:
    errors: list[str] = []
    for idx, row in enumerate(rows):
        for field in PROVENANCE_FIELDS:
            if blank(row.get(field, "")):
                errors.append(f"{table}[{idx}]: missing {field}")
    return errors


def check_identity(rows: list[dict[str, str]], table: str, fields: list[str]) -> list[str]:
    errors: list[str] = []
    for idx, row in enumerate(rows):
        for field in fields:
            if blank(row.get(field, "")):
                errors.append(f"{table}[{idx}]: missing {field}")
    return errors


def check_unique(rows: list[dict[str, str]], table: str, fields: list[str]) -> list[str]:
    seen: dict[tuple[str, ...], int] = {}
    errors: list[str] = []
    for idx, row in enumerate(rows):
        key = tuple(str(row.get(field, "")).strip() for field in fields)
        if any(blank(part) for part in key):
            continue
        if key in seen:
            errors.append(f"{table}[{idx}]: duplicate key {fields}={key}; first_seen={seen[key]}")
        seen[key] = idx
    return errors


def check_winners(results: list[dict[str, str]]) -> list[str]:
    races = {str(row.get("race_id", "")).strip() for row in results if not blank(row.get("race_id", ""))}
    winners: dict[str, int] = {}
    for row in results:
        race_id = str(row.get("race_id", "")).strip()
        finish = str(row.get("finish_position", "")).strip().upper()
        if race_id and finish.split()[0:1] == ["1"]:
            winners[race_id] = winners.get(race_id, 0) + 1
    return [f"results: race_id={race_id} winner_count=0" for race_id in sorted(races) if winners.get(race_id, 0) < 1]


def check_feature_store(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    header = read_header(path)
    if not header:
        return errors, warnings
    tags = build_feature_tags(header)
    post_cols = [name for name, tag in tags.items() if tag == POST_RACE_ONLY]
    if post_cols:
        errors.append(f"post_race_columns_in_feature_store={post_cols}")
    research_cols = [name for name, tag in tags.items() if tag == RESEARCH_ONLY]
    if research_cols:
        warnings.append(f"research_only_columns_in_feature_store={research_cols}")
    rows = load_csv(path)
    errors.extend(check_identity(rows, "feature_store", ["race_id", "runner_id"]))
    errors.extend(check_unique(rows, "feature_store", ["runner_id"]))
    return errors, warnings


def check_scaffold_outputs(rows: list[dict[str, str]], table: str) -> list[str]:
    errors: list[str] = []
    if not rows:
        return errors
    for idx, row in enumerate(rows):
        for field, expected in SCAFFOLD_REQUIRED.items():
            if field in row and str(row.get(field, "")).strip() != expected:
                errors.append(f"{table}[{idx}]: {field} must be {expected}")
        for field in ["stake_fraction_allowed", "fractional_kelly_25"]:
            if field in row and not blank(row.get(field, "")):
                try:
                    stake = float(str(row.get(field, "0")).strip())
                except ValueError:
                    errors.append(f"{table}[{idx}]: {field} is not numeric")
                    continue
                if stake != 0.0:
                    errors.append(f"{table}[{idx}]: {field} must be 0.0 for scaffold outputs")
    return errors


def main() -> int:
    processed = REPO_ROOT / "data" / "processed" / "hkjc"
    errors: list[str] = []
    warnings: list[str] = []

    for name in GOVERNANCE_FILES:
        if not (REPO_ROOT / name).exists():
            errors.append(f"missing governance file: {name}")

    races = load_csv(processed / "races.csv")
    runners = load_csv(processed / "runners.csv")
    results = load_csv(processed / "results.csv")
    dividends = load_csv(processed / "dividends.csv")

    for table, rows in [("races", races), ("runners", runners), ("results", results), ("dividends", dividends)]:
        errors.extend(check_provenance(rows, table))
    errors.extend(check_identity(races, "races", ["race_id"]))
    errors.extend(check_identity(runners, "runners", ["race_id", "runner_id"]))
    errors.extend(check_identity(results, "results", ["race_id", "runner_id"]))
    errors.extend(check_unique(races, "races", ["race_id"]))
    errors.extend(check_unique(runners, "runners", ["runner_id"]))
    errors.extend(check_unique(results, "results", ["runner_id"]))
    errors.extend(check_winners(results))

    feature_errors, feature_warnings = check_feature_store(processed / "feature_store.csv")
    errors.extend(feature_errors)
    warnings.extend(feature_warnings)

    errors.extend(check_scaffold_outputs(load_csv(processed / "model_probabilities.csv"), "model_probabilities"))
    errors.extend(check_scaffold_outputs(load_csv(processed / "betting_ev_simulation.csv"), "betting_ev_simulation"))

    registry_rows = load_csv(processed / "source_registry.csv")
    registry_issues = validate_source_registry_rows(registry_rows)
    registry_status = validation_summary(registry_issues)
    errors.extend(str(issue) for issue in registry_issues)

    status = "pass" if not errors else "fail"
    report_path = REPO_ROOT / "reports" / "extraction_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## Validation Run ({datetime.now(UTC).isoformat()})\n")
        handle.write(f"- status: {status}\n")
        handle.write(f"- validation_errors: {len(errors)}\n")
        handle.write(f"- warnings: {len(warnings)}\n")
        handle.write(f"- registry_validation: {registry_status}\n")
        for item in errors[:30]:
            handle.write(f"  - {item}\n")
        for item in warnings[:30]:
            handle.write(f"  - warning: {item}\n")

    print(f"validation_status={status}")
    print(f"validation_errors={len(errors)}")
    print(f"leakage_issues={len(feature_errors)}")
    print(f"warnings={len(warnings)}")
    print(f"registry_validation={registry_status}")
    print(f"races_rows={len(races)}")
    print(f"runners_rows={len(runners)}")
    print(f"results_rows={len(results)}")
    print(f"dividends_rows={len(dividends)}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
