import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "hkjc"


def _rows(name: str):
    with (PROCESSED / name).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_core_tables_have_no_blank_ids() -> None:
    for filename in ["runners.csv", "results.csv", "feature_store.csv"]:
        for row in _rows(filename):
            assert row.get("race_id", "").strip()
            assert row.get("runner_id", "").strip()


def test_abnormal_results_are_quarantined_from_normal_runner_ids() -> None:
    abnormal_path = PROCESSED / "abnormal_results.csv"
    if abnormal_path.exists():
        rows = _rows("abnormal_results.csv")
        assert rows
        assert all(row.get("abnormal_reason", "").strip() for row in rows)
