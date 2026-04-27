from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from src.hkjc.parse_results import ParserLayoutError


def _clean(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _race_id_from_url(source_url: str) -> str:
    query = parse_qs(urlparse(source_url).query)
    race_date = query.get("racedate", [""])[0].replace("/", "-")
    racecourse = query.get("Racecourse", [""])[0]
    race_no = query.get("RaceNo", [""])[0]
    return "-".join([part for part in [race_date, racecourse, race_no] if part])


def parse_dividends_page(
    *,
    html: str,
    source_url: str,
    extraction_timestamp: str,
) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    dividend_table = soup.select_one(".dividend_tab table")
    if not dividend_table:
        raise ParserLayoutError("Dividend table was not found")

    race_id = _race_id_from_url(source_url)
    rows = dividend_table.select("tr")
    if len(rows) <= 2:
        raise ParserLayoutError("Dividend table does not contain expected data rows")

    dividends: list[dict[str, str]] = []
    last_pool_type = ""

    for tr in rows[2:]:
        cells = [_clean(cell.get_text(" ", strip=True)) for cell in tr.select("td")]
        if len(cells) < 2:
            continue

        pool_type = ""
        winning_combination = ""
        dividend = ""
        if len(cells) >= 3:
            pool_type = cells[0] if cells[0] else last_pool_type
            winning_combination = cells[1]
            dividend = cells[2]
        else:
            pool_type = last_pool_type
            winning_combination = cells[0]
            dividend = cells[1]

        if pool_type:
            last_pool_type = pool_type

        dividends.append(
            {
                "source_url": source_url,
                "source_name": "HKJC",
                "source_page_type": "Dividends",
                "extraction_timestamp": extraction_timestamp,
                "race_id": race_id,
                "pool_type": pool_type,
                "winning_combination": winning_combination,
                "dividend": dividend,
                "raw_value": "|".join(cells),
            }
        )

    return dividends
