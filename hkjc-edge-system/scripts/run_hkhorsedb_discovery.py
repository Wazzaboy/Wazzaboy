#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.logging_utils import ensure_log_files
from src.hkhorsedb.discovery import discover_hkhorsedb_sources, write_factor_availability, write_source_registry


def main() -> int:
    logs_dir = REPO_ROOT / "logs"
    processed_dir = REPO_ROOT / "data" / "processed" / "hkhorsedb"
    reports_path = REPO_ROOT / "reports" / "hkhorsedb_enrichment_report.md"

    ensure_log_files(logs_dir)
    entries = discover_hkhorsedb_sources(logs_dir)

    write_source_registry(entries, processed_dir / "source_registry.csv")
    write_factor_availability(entries, processed_dir / "factor_availability.csv")

    restricted = sum(1 for e in entries if e.access_status == "restricted")
    with reports_path.open("w", encoding="utf-8") as handle:
        handle.write("# HKHorseDB Enrichment Report\n\n")
        handle.write(f"- discovered_sources: {len(entries)}\n")
        handle.write(f"- restricted_sources: {restricted}\n")
        handle.write("- note: HKHorseDB is secondary and never overwrites HKJC official records.\n")

    print(f"discovered_sources={len(entries)}")
    print(f"restricted_sources={restricted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
