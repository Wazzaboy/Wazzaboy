"""Validate key processed files against required schemas."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.validation import REQUIRED_SCHEMAS, validate_csv_file

PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed"


def main() -> None:
    table_paths = {
        "races": PROCESSED_ROOT / "hkjc" / "races.csv",
        "runners": PROCESSED_ROOT / "hkjc" / "runners.csv",
        "dividends": PROCESSED_ROOT / "hkjc" / "dividends.csv",
        "odds_snapshots": PROCESSED_ROOT / "hkjc" / "odds_snapshots.csv",
        "factor_availability": PROCESSED_ROOT / "hkjc" / "factor_availability.csv",
    }

    for table_name, path in table_paths.items():
        result = validate_csv_file(table_name, path)
        if result.valid:
            print(f"PASS {table_name}: {path}")
        else:
            missing = ", ".join(result.missing_columns)
            print(f"FAIL {table_name}: missing columns -> {missing}")

    print(f"Validated {len(REQUIRED_SCHEMAS)} table schema definitions.")


if __name__ == "__main__":
    main()
