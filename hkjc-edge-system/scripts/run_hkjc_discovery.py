#!/usr/bin/env python3
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import csv
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.logging_utils import ensure_log_files
from src.hkjc.discovery import discover_sources, source_registry_sample, write_discovery_outputs


def _append_extraction_report(report_path: Path, summary: str, issue_count: int, sample_rows: list[dict[str, str]]) -> None:
    timestamp = datetime.now(UTC).isoformat()
    sample_lines = "\n".join(
        f"- {row['source_name']} | {row['source_page_type']} | {row['access_status']} | {row['source_url']}"
        for row in sample_rows
    )
    if not sample_lines:
        sample_lines = "- (no rows)"

    snippet = (
        f"\n## Discovery Run ({timestamp})\n"
        f"- validation_status: {summary}\n"
        f"- validation_issues: {issue_count}\n"
        f"- source_registry_sample:\n{sample_lines}\n"
    )
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write(snippet)


def main() -> int:
    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"
    logs_dir = REPO_ROOT / "logs"
    reports_dir = REPO_ROOT / "reports"

    ensure_log_files(logs_dir)

    registry_path = processed_dir / "source_registry.csv"
    validation_path = processed_dir / "source_registry_validation.csv"
    report_path = reports_dir / "extraction_report.md"

    entries = discover_sources()
    summary, issue_count = write_discovery_outputs(entries, registry_path, validation_path)

    sample_rows = source_registry_sample(registry_path)
    _append_extraction_report(report_path, summary, issue_count, sample_rows)

    print(f"registry_path={registry_path}")
    print(f"validation_path={validation_path}")
    print(f"validation_status={summary}")
    print(f"validation_issues={issue_count}")
    print("source_registry_sample=")
    for row in sample_rows:
        print(row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
