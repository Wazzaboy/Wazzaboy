#!/usr/bin/env python3
"""Entry point for a single-session HKJC results extraction run.

Discovers recent result URLs from the HKJC website and parses them into
structured CSV outputs under data/processed/hkjc/. Delegates to the
full extraction module for all parsing and I/O logic.

Usage:
    python scripts/run_hkjc_extraction.py [--limit N] [--url URL ...]

For historical backfill over a date range use:
    python scripts/run_hkjc_results_extraction.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_hkjc_results_extraction import main

if __name__ == "__main__":
    raise SystemExit(main())
