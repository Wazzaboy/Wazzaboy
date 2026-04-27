from __future__ import annotations

from src.hkjc.parse_results import ParserLayoutError, parse_results_page


RESULTS_HTML = """
<div class="localResults commContent">
  <div class="race_tab">
    <table>
      <tr><td>RACE 1 (634)</td><td></td><td></td></tr>
      <tr><td></td><td></td><td></td></tr>
      <tr><td>Class 4 - 1200M - (60-40)</td><td>Going :</td><td>GOOD TO FIRM</td></tr>
      <tr><td>FWD INSURANCE ACT PRIVATE HANDICAP</td><td>Course :</td><td>TURF - \"A\" Course</td></tr>
      <tr><td>HK$ 1,170,000</td><td>Time :</td><td>(23.33)</td></tr>
    </table>
  </div>
  <table class="f_tac table_bd draggable">
    <tr>
      <td>Pla.</td><td>Horse No.</td><td>Horse</td><td>Jockey</td><td>Trainer</td>
      <td>Act. Wt.</td><td>Declar. Horse Wt.</td><td>Dr.</td><td>LBW</td>
      <td>Running Position</td><td>Finish Time</td><td>Win Odds</td>
    </tr>
    <tr>
      <td>1</td><td>13</td><td>PACKING KING (K570)</td><td>Z Purton</td><td>C S Shum</td>
      <td>122</td><td>1133</td><td>8</td><td>-</td><td>5 5 1</td><td>1:08.70</td><td>3.3</td>
    </tr>
    <tr>
      <td>2</td><td>9</td><td>LUCRATIVE EIGHT (K542)</td><td>K Teetan</td><td>P F Yiu</td>
      <td>126</td><td>1102</td><td>1</td><td>N</td><td>4 3 2</td><td>1:08.75</td><td>4.8</td>
    </tr>
  </table>
</div>
"""


def test_parse_results_page_extracts_race_runner_and_result_rows() -> None:
    parsed = parse_results_page(
        html=RESULTS_HTML,
        source_url="https://racing.hkjc.com/en-us/local/information/localresults?racedate=2026/04/26&Racecourse=ST&RaceNo=1",
        extraction_timestamp="2026-04-27T00:00:00+00:00",
    )

    assert len(parsed.races) == 1
    assert parsed.races[0]["race_id"] == "2026-04-26-ST-1"
    assert parsed.races[0]["field_size"] == "2"
    assert parsed.races[0]["source_name"] == "HKJC"

    assert len(parsed.runners) == 2
    assert parsed.runners[0]["horse_name"] == "PACKING KING"
    assert parsed.runners[0]["horse_id_or_brand_no"] == "K570"
    assert parsed.runners[1]["odds"] == "4.8"

    assert len(parsed.results) == 2
    assert parsed.results[0]["finish_position"] == "1"
    assert parsed.results[0]["source_page_type"] == "Results"


def test_parse_results_page_raises_layout_error_when_expected_tables_missing() -> None:
    bad_html = "<html><body><div>no local results</div></body></html>"
    try:
        parse_results_page(
            html=bad_html,
            source_url="https://racing.hkjc.com/en-us/local/information/localresults?racedate=2026/04/26&Racecourse=ST&RaceNo=1",
            extraction_timestamp="2026-04-27T00:00:00+00:00",
        )
        raise AssertionError("Expected ParserLayoutError")
    except ParserLayoutError:
        pass
