from pathlib import Path

from src.common.validation import validate_columns, validate_csv_file


def test_validate_columns_detects_missing() -> None:
    result = validate_columns(["source_url", "source_name"], ["source_url", "source_name", "race_id"])
    assert not result.valid
    assert result.missing_columns == ("race_id",)


def test_validate_csv_file_for_dividends(tmp_path: Path) -> None:
    csv_path = tmp_path / "dividends.csv"
    csv_path.write_text(
        "source_url,source_name,extraction_timestamp,race_id,pool_type,winning_combination,dividend,raw_value\n",
        encoding="utf-8",
    )
    result = validate_csv_file("dividends", csv_path)
    assert result.valid
