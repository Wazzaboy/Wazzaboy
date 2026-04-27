from __future__ import annotations

from datetime import date

from src.hkjc.race_index import build_date_results_url, extract_race_result_urls_from_date_page


def test_build_date_results_url() -> None:
    target = date(2026, 4, 26)
    url = build_date_results_url(target)
    assert "localresults?racedate=2026%2F04%2F26" in url


def test_extract_race_result_urls_filters_to_requested_date_and_has_race_fields() -> None:
    html = """
    <html><body>
      <a href="/en-us/local/information/localresults?racedate=2026/04/26&Racecourse=ST&RaceNo=1">Race 1</a>
      <a href="/en-us/local/information/localresults?racedate=2026/04/26&Racecourse=ST&RaceNo=2">Race 2</a>
      <a href="/en-us/local/information/localresults?racedate=2026/04/20&Racecourse=ST&RaceNo=1">Other date</a>
      <a href="/en-us/local/information/localresults?racedate=2026/04/26">Missing fields</a>
    </body></html>
    """

    urls = extract_race_result_urls_from_date_page(
        html=html,
        requested_date=date(2026, 4, 26),
        base_url="https://racing.hkjc.com/en-us/local/information/localresults?racedate=2026/04/26",
    )

    assert len(urls) == 2
    assert all("racedate=2026/04/26" in url for url in urls)
    assert all("RaceNo=" in url for url in urls)
