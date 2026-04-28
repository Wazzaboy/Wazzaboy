import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rows(path: Path):
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_betting_ev_simulation_has_no_actionable_stake() -> None:
    rows = _rows(ROOT / "data" / "processed" / "hkjc" / "betting_ev_simulation.csv")
    for row in rows:
        assert row.get("bet_signal_status") == "blocked_scaffold_only"
        assert row.get("stake_permission") == "not_allowed_placeholder_model"
        assert float(row.get("stake_fraction_allowed", "0") or 0) == 0.0


def test_model_readiness_report_blocks_production_status() -> None:
    text = (ROOT / "reports" / "model_readiness_report.md").read_text(encoding="utf-8")
    assert "structural_scaffold_only" in text
    assert "thresholds_passed: false" in text
    assert "No bet recommendations can be derived" in text
