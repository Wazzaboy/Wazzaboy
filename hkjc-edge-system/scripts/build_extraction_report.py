#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def _count_log_rows(path: Path) -> int:
    return _count_rows(path)


def main() -> int:
    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"
    logs_dir = REPO_ROOT / "logs"
    report_path = REPO_ROOT / "reports" / "extraction_report.md"

    tables = {
        "races": processed_dir / "races.csv",
        "runners": processed_dir / "runners.csv",
        "results": processed_dir / "results.csv",
        "dividends": processed_dir / "dividends.csv",
        "comments": processed_dir / "comments.csv",
        "incidents": processed_dir / "incidents.csv",
        "race_cards": processed_dir / "race_cards.csv",
        "changes": processed_dir / "changes.csv",
        "race_index": processed_dir / "race_index.csv",
        "feature_store": processed_dir / "feature_store.csv",
    }
    counts = {name: _count_rows(path) for name, path in tables.items()}

    logs = {
        "missing_data": logs_dir / "missing_data_log.csv",
        "parser_errors": logs_dir / "parser_error_log.csv",
        "restricted_pages": logs_dir / "restricted_pages_log.csv",
        "conflicts": logs_dir / "conflict_log.csv",
    }
    log_counts = {name: _count_log_rows(path) for name, path in logs.items()}

    timestamp = datetime.now(UTC).isoformat()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## Extraction Report ({timestamp})\n")
        handle.write("### Processed data row counts\n")
        for name, count in counts.items():
            handle.write(f"- {name}: {count}\n")
        handle.write("### Log row counts\n")
        for name, count in log_counts.items():
            handle.write(f"- {name}: {count}\n")

    print(f"report_path={report_path}")
    for name, count in counts.items():
        print(f"{name}_rows={count}")
    for name, count in log_counts.items():
        print(f"{name}_log_rows={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
