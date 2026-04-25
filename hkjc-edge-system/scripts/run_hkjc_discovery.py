"""Run HKJC public-source discovery and persist outputs."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.validation import validate_records
from src.hkjc.discovery import audit_discovery, discover_hkjc_public_pages, discovery_summary, persist_discovery


def main() -> None:
    output_csv = PROJECT_ROOT / "data" / "processed" / "hkjc" / "source_discovery.csv"
    logs_dir = PROJECT_ROOT / "logs"

    rows = discover_hkjc_public_pages()
    persist_discovery(rows, output_csv)
    audit_discovery(rows, logs_dir)

    summary = discovery_summary(rows)
    validation = validate_records("source_discovery", rows)

    print(f"Discovery rows: {summary['row_count']}")
    print(f"Status counts: {summary['status_counts']}")
    print(f"Output CSV: {output_csv}")
    print(f"Validation valid: {validation.valid}")
    if not validation.valid:
        print(f"Missing columns: {validation.missing_columns}")


if __name__ == "__main__":
    main()
