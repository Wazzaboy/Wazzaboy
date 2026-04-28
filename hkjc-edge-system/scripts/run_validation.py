#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.source_registry import REQUIRED_SOURCE_FIELDS
from src.common.validation import validate_source_registry_rows, validation_summary
from src.features.leakage_tags import POST_RACE_ONLY, build_feature_tags


_PROVENANCE_FIELDS = [
    "source_url",
    "source_name",
    "source_page_type",
    "extraction_timestamp",
]


def _load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _check_provenance(rows: list[dict[str, str]], table_name: str) -> list[str]:
    errors: list[str] = []
    for idx, row in enumerate(rows):
        for field in _PROVENANCE_FIELDS:
            value = str(row.get(field, "")).strip()
            if not value or value == "NULL":
                errors.append(f"{table_name}[{idx}]: missing {field}")
    return errors


def main() -> int:
    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"
    report_path = REPO_ROOT / "reports" / "extraction_report.md"

    races = _load_csv(processed_dir / "races.csv")
    runners = _load_csv(processed_dir / "runners.csv")
    results = _load_csv(processed_dir / "results.csv")
    dividends = _load_csv(processed_dir / "dividends.csv")
    feature_store_path = processed_dir / "feature_store.csv"

    all_errors: list[str] = []
    all_errors.extend(_check_provenance(races, "races"))
    all_errors.extend(_check_provenance(runners, "runners"))
    all_errors.extend(_check_provenance(results, "results"))
    all_errors.extend(_check_provenance(dividends, "dividends"))

    # Leakage check on feature store columns
    leakage_issues: list[str] = []
    if feature_store_path.exists():
        import pandas as pd
        feature_store = pd.read_csv(feature_store_path, nrows=0)
        tags = build_feature_tags(feature_store.columns)
        leakage_cols = [name for name, tag in tags.items() if tag == POST_RACE_ONLY]
        if leakage_cols:
            leakage_issues.append(f"post_race_columns_in_feature_store={leakage_cols}")

    # Source registry validation
    registry_rows = _load_csv(processed_dir / "source_registry.csv")
    registry_issues = validate_source_registry_rows(registry_rows)
    registry_status = validation_summary(registry_issues)

    overall_pass = not all_errors and not leakage_issues and not registry_issues
    status = "pass" if overall_pass else "fail"

    timestamp = datetime.now(UTC).isoformat()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## Validation Run ({timestamp})\n")
        handle.write(f"- status: {status}\n")
        handle.write(f"- provenance_errors: {len(all_errors)}\n")
        handle.write(f"- leakage_issues: {len(leakage_issues)}\n")
        handle.write(f"- registry_validation: {registry_status}\n")
        for err in all_errors[:20]:
            handle.write(f"  - {err}\n")
        for issue in leakage_issues:
            handle.write(f"  - {issue}\n")

    print(f"validation_status={status}")
    print(f"provenance_errors={len(all_errors)}")
    print(f"leakage_issues={len(leakage_issues)}")
    print(f"registry_validation={registry_status}")
    print(f"races_rows={len(races)}")
    print(f"runners_rows={len(runners)}")
    print(f"results_rows={len(results)}")
    print(f"dividends_rows={len(dividends)}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
