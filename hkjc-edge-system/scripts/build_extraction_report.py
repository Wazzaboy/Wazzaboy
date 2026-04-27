"""Build simple extraction report from log files."""

from __future__ import annotations

import sys
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
LOGS_DIR = PROJECT_ROOT / "logs"
REPORT_PATH = PROJECT_ROOT / "reports" / "extraction_report.md"


def row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    return max(0, len(rows) - 1)


def main() -> None:
    counts = {
        "missing_data_log.csv": row_count(LOGS_DIR / "missing_data_log.csv"),
        "parser_error_log.csv": row_count(LOGS_DIR / "parser_error_log.csv"),
        "restricted_pages_log.csv": row_count(LOGS_DIR / "restricted_pages_log.csv"),
        "conflict_log.csv": row_count(LOGS_DIR / "conflict_log.csv"),
    }

    lines = ["# Extraction Report", "", "## Log row counts", ""]
    for name, count in counts.items():
        lines.append(f"- `{name}`: {count}")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report written: {REPORT_PATH}")


if __name__ == "__main__":
    main()
