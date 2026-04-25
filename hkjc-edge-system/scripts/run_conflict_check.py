"""Lightweight conflict log checker."""

from __future__ import annotations

import sys
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
CONFLICT_LOG = PROJECT_ROOT / "logs" / "conflict_log.csv"


def main() -> None:
    if not CONFLICT_LOG.exists():
        print("No conflict log found.")
        return

    with CONFLICT_LOG.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    severe = [row for row in rows if row.get("severity", "").lower() in {"high", "critical"}]
    print(f"Total conflicts: {len(rows)}")
    print(f"High/Critical conflicts: {len(severe)}")


if __name__ == "__main__":
    main()
