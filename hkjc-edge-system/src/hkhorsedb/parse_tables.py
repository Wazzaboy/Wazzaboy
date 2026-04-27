from __future__ import annotations

from bs4 import BeautifulSoup


def _clean(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _rows_from_tables(html: str) -> list[list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[list[str]] = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [_clean(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])]
            if len(cells) >= 2:
                rows.append(cells)
    return rows


def parse_hkhorsedb_tables(*, html: str, source_url: str, source_page_type: str, extraction_timestamp: str) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    rows = _rows_from_tables(html)

    horses: list[dict[str, str]] = []
    races: list[dict[str, str]] = []
    runners: list[dict[str, str]] = []

    for idx, row in enumerate(rows):
        text = " ".join(row).lower()
        payload = {
            "source_url": source_url,
            "source_name": "HKHorseDB",
            "source_page_type": source_page_type,
            "extraction_timestamp": extraction_timestamp,
            "raw_value": "|".join(row),
        }
        if "horse" in text and len(horses) < 200:
            horses.append({**payload, "horse_key": f"horse_row_{idx}", "horse_name": row[0]})
        if "race" in text and len(races) < 200:
            races.append({**payload, "race_key": f"race_row_{idx}", "race_name": row[0]})
        if any(token in text for token in ["jockey", "trainer", "runner"]) and len(runners) < 200:
            runners.append({**payload, "runner_key": f"runner_row_{idx}", "runner_name": row[0]})

    return horses, races, runners
