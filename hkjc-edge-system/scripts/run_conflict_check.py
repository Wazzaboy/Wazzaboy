#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_cross_source_conflict_check import run_conflict_check


def main() -> int:
    conflicts = run_conflict_check(REPO_ROOT)
    print(f"conflicts_logged={conflicts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
