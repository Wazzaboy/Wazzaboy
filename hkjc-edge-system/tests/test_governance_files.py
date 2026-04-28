from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_governance_files_exist_and_block_production_claims() -> None:
    for name in ["EDGE_DOCTRINE.md", "LEAKAGE_POLICY.md", "SOURCE_REGISTRY.yaml"]:
        path = ROOT / name
        assert path.exists(), f"missing {name}"
    doctrine = (ROOT / "EDGE_DOCTRINE.md").read_text(encoding="utf-8")
    assert "structural_scaffold_only" in doctrine
    assert "No row may be interpreted as a production bet" in doctrine
