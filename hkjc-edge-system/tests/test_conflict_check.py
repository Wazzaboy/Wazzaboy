from __future__ import annotations

from pathlib import Path

from scripts.run_cross_source_conflict_check import run_conflict_check
from src.common.logging_utils import ensure_log_files


def test_conflict_check_logs_non_matching_horse(tmp_path: Path) -> None:
    (tmp_path / "data" / "processed" / "hkjc").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "processed" / "hkhorsedb").mkdir(parents=True, exist_ok=True)

    (tmp_path / "data" / "processed" / "hkjc" / "runners.csv").write_text(
        "horse_name\nPACKING KING\n",
        encoding="utf-8",
    )
    (tmp_path / "data" / "processed" / "hkhorsedb" / "runners.csv").write_text(
        "runner_key,runner_name,source_url\nrow1,OTHER HORSE,https://example.com\n",
        encoding="utf-8",
    )

    ensure_log_files(tmp_path / "logs")
    conflicts = run_conflict_check(tmp_path)

    assert conflicts == 1
    conflict_log = (tmp_path / "logs" / "conflict_log.csv").read_text(encoding="utf-8")
    assert "OTHER HORSE" in conflict_log
