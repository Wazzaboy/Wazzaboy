from __future__ import annotations

from src.hkjc.parse_dividends import parse_dividends_page
from src.hkjc.parse_results import ParserLayoutError


DIVIDENDS_HTML = """
<div class="localResults commContent">
  <div class="dividend_tab">
    <table>
      <tr><td>Dividend</td></tr>
      <tr><td>Pool</td><td>Winning Combination</td><td>Dividend (HK$)</td></tr>
      <tr><td>WIN</td><td>13</td><td>33.50</td></tr>
      <tr><td>PLACE</td><td>13</td><td>14.50</td></tr>
      <tr><td>9</td><td>17.00</td></tr>
    </table>
  </div>
</div>
"""


def test_parse_dividends_page_extracts_rows_and_carries_pool_type() -> None:
    rows = parse_dividends_page(
        html=DIVIDENDS_HTML,
        source_url="https://racing.hkjc.com/en-us/local/information/localresults?racedate=2026/04/26&Racecourse=ST&RaceNo=1",
        extraction_timestamp="2026-04-27T00:00:00+00:00",
    )

    assert len(rows) == 3
    assert rows[0]["pool_type"] == "WIN"
    assert rows[1]["pool_type"] == "PLACE"
    assert rows[2]["pool_type"] == "PLACE"
    assert rows[2]["winning_combination"] == "9"
    assert rows[2]["dividend"] == "17.00"
    assert rows[0]["race_id"] == "2026-04-26-ST-1"


def test_parse_dividends_page_raises_layout_error_when_table_missing() -> None:
    try:
        parse_dividends_page(
            html="<html><body></body></html>",
            source_url="https://racing.hkjc.com/en-us/local/information/localresults?racedate=2026/04/26&Racecourse=ST&RaceNo=1",
            extraction_timestamp="2026-04-27T00:00:00+00:00",
        )
        raise AssertionError("Expected ParserLayoutError")
    except ParserLayoutError:
        pass
