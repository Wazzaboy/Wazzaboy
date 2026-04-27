#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.features.build_feature_store import build_feature_store


def main() -> int:
    processed_dir = REPO_ROOT / "data" / "processed" / "hkjc"
    stats = build_feature_store(processed_dir)
    print(f"feature_store_path={stats.output_path}")
    print(f"feature_manifest_path={stats.manifest_path}")
    print(f"rows={stats.rows}")
    print(f"races={stats.races}")
    print(f"missing_odds_rows={stats.missing_odds_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
