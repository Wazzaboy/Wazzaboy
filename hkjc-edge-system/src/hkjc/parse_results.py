from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup


class ParserLayoutError(ValueError):
    """Raised when expected HKJC results layout elements cannot be found."""


@dataclass(frozen=True)
class ParsedResults:
    races: list[dict[str, str]]
    runners: list[dict[str, str]]
    results: list[dict[str, str]]
    abnormal_results: list[dict[str, str]]


def _clean(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _assert_date_format(race_date: str) -> None:
    try:
        datetime.strptime(race_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"invalid race_date format in URL: {race_date!r}") from exc


def _extract_race_context(source_url: str) -> tuple[str, str, str]:
    query = parse_qs(urlparse(source_url).query)
    race_date = query.get("racedate", [""])[0].replace("/", "-")
    racecourse = query.get("Racecourse", [""])[0]
    race_no = query.get("RaceNo", [""])[0]

    if race_date:
        _assert_date_format(race_date)

    return race_date, racecourse, race_no


def _extract_horse_fields(horse_raw: str) -> tuple[str, str]:
    match = re.match(r"^(.*?)\s*\(([^)]+)\)$", horse_raw)
    if not match:
        return horse_raw, ""
    return _clean(match.group(1)), _clean(match.group(2))


def _abnormal_result_row(
    *,
    source_url: str,
    extraction_timestamp: str,
    race_id: str,
    race_date: str,
    racecourse: str,
    race_no: str,
    horse_no: str,
    horse_name: str,
    finish_position: str,
    issue_type: str,
    raw_value: str,
) -> dict[str, str]:
    return {
        "source_url": source_url,
        "source_name": "HKJC",
        "source_page_type": "Results",
        "extraction_timestamp": extraction_timestamp,
        "race_id": race_id,
        "race_date": race_date,
        "racecourse": racecourse,
        "race_no": race_no,
        "horse_no": horse_no,
        "horse_name": horse_name,
        "finish_position": finish_position,
        "issue_type": issue_type,
        "parser_action": "excluded_from_normal_runner_and_result_tables",
        "raw_value": raw_value,
    }


def parse_results_page(
    *,
    html: str,
    source_url: str,
    extraction_timestamp: str,
) -> ParsedResults:
    soup = BeautifulSoup(html, "html.parser")
    local_results = soup.select_one("div.localResults")
    race_meta_table = soup.select_one(".race_tab table")
    runner_table = soup.select_one("table.draggable")

    if not local_results or not race_meta_table or not runner_table:
        raise ParserLayoutError("Expected HKJC local results tables were not found")

    race_date, racecourse, race_no_from_url = _extract_race_context(source_url)

    meta_rows = [[_clean(cell.get_text(" ", strip=True)) for cell in tr.select("td")] for tr in race_meta_table.select("tr")]
    if len(meta_rows) < 5:
        raise ParserLayoutError("Race metadata table does not contain expected rows")

    race_header = meta_rows[0][0] if meta_rows[0] else ""
    race_no_match = re.search(r"RACE\s+(\d+)", race_header)
    meeting_match = re.search(r"\((\d+)\)", race_header)

    race_no = race_no_from_url or (race_no_match.group(1) if race_no_match else "")
    meeting_id = meeting_match.group(1) if meeting_match else ""
    race_id = "-".join([part for part in [race_date, racecourse, race_no] if part])

    class_distance = meta_rows[2][0] if len(meta_rows[2]) > 0 else ""
    going = meta_rows[2][2] if len(meta_rows[2]) > 2 else ""
    race_name = meta_rows[3][0] if len(meta_rows[3]) > 0 else ""
    course = meta_rows[3][2] if len(meta_rows[3]) > 2 else ""
    prize_money = meta_rows[4][0] if len(meta_rows[4]) > 0 else ""

    distance_match = re.search(r"(\d+)M", class_distance)
    class_match = re.search(r"(Class\s*\d+)", class_distance, flags=re.IGNORECASE)
    rating_match = re.search(r"\(([^)]+)\)", class_distance)

    race_row = {
        "source_url": source_url,
        "source_name": "HKJC",
        "source_page_type": "Results",
        "extraction_timestamp": extraction_timestamp,
        "race_id": race_id,
        "meeting_id": meeting_id,
        "race_date": race_date,
        "racecourse": racecourse,
        "race_no": race_no,
        "race_name": race_name,
        "class": class_match.group(1) if class_match else "",
        "rating_band": rating_match.group(1) if rating_match else "",
        "distance": distance_match.group(1) if distance_match else "",
        "surface": "",
        "course": course,
        "going": going,
        "prize_money": prize_money,
        "field_size": "",
        "abnormal_result_count": "",
        "raw_class_distance": class_distance,
        "raw_race_header": race_header,
    }

    rows = runner_table.select("tr")
    if len(rows) <= 1:
        raise ParserLayoutError("Runner results table has no data rows")

    runners: list[dict[str, str]] = []
    results: list[dict[str, str]] = []
    abnormal_results: list[dict[str, str]] = []
    seen_runner_ids: set[str] = set()

    for tr in rows[1:]:
        cells = [_clean(cell.get_text(" ", strip=True)) for cell in tr.select("td")]
        if len(cells) < 12:
            continue

        horse_name, horse_id = _extract_horse_fields(cells[2])
        horse_no = cells[1]
        raw_value = "|".join(cells)

        if not horse_no:
            abnormal_results.append(
                _abnormal_result_row(
                    source_url=source_url,
                    extraction_timestamp=extraction_timestamp,
                    race_id=race_id,
                    race_date=race_date,
                    racecourse=racecourse,
                    race_no=race_no,
                    horse_no=horse_no,
                    horse_name=horse_name,
                    finish_position=cells[0],
                    issue_type="blank_horse_no",
                    raw_value=raw_value,
                )
            )
            continue

        runner_id = f"{race_id}-{horse_no}" if race_id else ""
        if not runner_id:
            abnormal_results.append(
                _abnormal_result_row(
                    source_url=source_url,
                    extraction_timestamp=extraction_timestamp,
                    race_id=race_id,
                    race_date=race_date,
                    racecourse=racecourse,
                    race_no=race_no,
                    horse_no=horse_no,
                    horse_name=horse_name,
                    finish_position=cells[0],
                    issue_type="blank_runner_id",
                    raw_value=raw_value,
                )
            )
            continue

        if runner_id in seen_runner_ids:
            abnormal_results.append(
                _abnormal_result_row(
                    source_url=source_url,
                    extraction_timestamp=extraction_timestamp,
                    race_id=race_id,
                    race_date=race_date,
                    racecourse=racecourse,
                    race_no=race_no,
                    horse_no=horse_no,
                    horse_name=horse_name,
                    finish_position=cells[0],
                    issue_type="duplicate_runner_id",
                    raw_value=raw_value,
                )
            )
            continue
        seen_runner_ids.add(runner_id)

        runner_row = {
            "source_url": source_url,
            "source_name": "HKJC",
            "source_page_type": "Results",
            "extraction_timestamp": extraction_timestamp,
            "runner_id": runner_id,
            "race_id": race_id,
            "race_date": race_date,
            "racecourse": racecourse,
            "race_no": race_no,
            "horse_no": horse_no,
            "horse_name": horse_name,
            "horse_id_or_brand_no": horse_id,
            "draw": cells[7],
            "jockey": cells[3],
            "trainer": cells[4],
            "carried_weight": cells[5],
            "handicap_rating": "",
            "rating_change": "",
            "declared_body_weight": cells[6],
            "body_weight_change": "",
            "gear": "",
            "gear_change": "",
            "odds": cells[11],
            "finish_position": cells[0],
            "beaten_margin": cells[8],
            "race_time": cells[10],
            "sectional_time": "",
            "running_position": cells[9],
            "comments_or_notes": "",
            "raw_horse": cells[2],
            "raw_finish_time": cells[10],
            "raw_running_position": cells[9],
        }
        runners.append(runner_row)

        results.append(
            {
                "source_url": source_url,
                "source_name": "HKJC",
                "source_page_type": "Results",
                "extraction_timestamp": extraction_timestamp,
                "race_id": race_id,
                "runner_id": runner_id,
                "horse_no": horse_no,
                "horse_name": horse_name,
                "finish_position": cells[0],
                "beaten_margin": cells[8],
                "finish_time": cells[10],
                "running_position": cells[9],
                "win_odds": cells[11],
                "raw_value": raw_value,
            }
        )

    race_row["field_size"] = str(len(runners))
    race_row["abnormal_result_count"] = str(len(abnormal_results))

    return ParsedResults(races=[race_row], runners=runners, results=results, abnormal_results=abnormal_results)
