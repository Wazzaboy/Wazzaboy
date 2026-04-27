from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
import csv
from typing import Iterable

REQUIRED_SOURCE_FIELDS: tuple[str, ...] = (
    "source_url",
    "source_name",
    "source_page_type",
    "access_status",
    "model_value",
    "leakage_risk",
    "parser_difficulty",
    "notes",
)


@dataclass(frozen=True)
class SourceRegistryEntry:
    source_url: str
    source_name: str
    source_page_type: str
    access_status: str
    model_value: str
    leakage_risk: str
    parser_difficulty: str
    notes: str = ""
    extraction_timestamp: str = ""

    def to_dict(self) -> dict[str, str]:
        payload = asdict(self)
        if not payload["extraction_timestamp"]:
            payload["extraction_timestamp"] = datetime.now(UTC).isoformat()
        return payload


def required_registry_columns() -> list[str]:
    return list(REQUIRED_SOURCE_FIELDS) + ["extraction_timestamp"]


def default_hkjc_page_groups() -> list[SourceRegistryEntry]:
    return [
        SourceRegistryEntry(
            source_url="https://racing.hkjc.com/en-us/local/information/localresults",
            source_name="HKJC",
            source_page_type="Results",
            access_status="unknown",
            model_value="high",
            leakage_risk="post_race_only",
            parser_difficulty="medium",
            notes="Primary official results page. Use racedate/Racecourse/RaceNo query params for specific races.",
        ),
        SourceRegistryEntry(
            source_url="https://racing.hkjc.com/en-us/local/information/racecard",
            source_name="HKJC",
            source_page_type="Race Card",
            access_status="unknown",
            model_value="high",
            leakage_risk="low",
            parser_difficulty="medium",
            notes="Primary pre-race declarations and entries.",
        ),
        SourceRegistryEntry(
            source_url="https://bet.hkjc.com/racing/pages/odds_wp.aspx",
            source_name="HKJC",
            source_page_type="Current Odds",
            access_status="unknown",
            model_value="high",
            leakage_risk="time_sensitive",
            parser_difficulty="high",
            notes="Public odds board; requires timestamped snapshots.",
        ),
        SourceRegistryEntry(
            source_url="https://racing.hkjc.com/en-us/local/information/dividend",
            source_name="HKJC",
            source_page_type="Dividends",
            access_status="unknown",
            model_value="medium",
            leakage_risk="post_race_only",
            parser_difficulty="medium",
            notes="Dividend pools and pay-outs.",
        ),
        SourceRegistryEntry(
            source_url="https://racing.hkjc.com/en-us/local/information/changes",
            source_name="HKJC",
            source_page_type="Changes",
            access_status="unknown",
            model_value="medium",
            leakage_risk="low",
            parser_difficulty="low",
            notes="Late gear/rider/runner changes.",
        ),
        SourceRegistryEntry(
            source_url="https://racing.hkjc.com/en-us/horse/vetRecords",
            source_name="HKJC",
            source_page_type="Veterinary Records",
            access_status="unknown",
            model_value="medium",
            leakage_risk="mixed",
            parser_difficulty="medium",
            notes="Use historically for future races only.",
        ),
        SourceRegistryEntry(
            source_url="https://racing.hkjc.com/en-us/local/information/trackwork",
            source_name="HKJC",
            source_page_type="Trackwork",
            access_status="unknown",
            model_value="medium",
            leakage_risk="low",
            parser_difficulty="medium",
            notes="Public trackwork tables when published.",
        ),
        SourceRegistryEntry(
            source_url="https://racing.hkjc.com/en-us/local/information/racereportfull",
            source_name="HKJC",
            source_page_type="Race Report",
            access_status="unknown",
            model_value="medium",
            leakage_risk="post_race_only",
            parser_difficulty="medium",
            notes="Post-race official reporting pages including incident and comments on running.",
        ),
        SourceRegistryEntry(
            source_url="https://racing.hkjc.com/en-us/racing/fixture",
            source_name="HKJC",
            source_page_type="Fixtures",
            access_status="unknown",
            model_value="low",
            leakage_risk="low",
            parser_difficulty="low",
            notes="Top-level fixture and schedule navigation.",
        ),
        SourceRegistryEntry(
            source_url="https://www.hkhorsedb.com/",
            source_name="HKHorseDB",
            source_page_type="Secondary Enrichment",
            access_status="placeholder",
            model_value="secondary",
            leakage_risk="review_required",
            parser_difficulty="unknown",
            notes="Secondary source only; never overrides HKJC.",
        ),
    ]


def write_source_registry(entries: Iterable[SourceRegistryEntry], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=required_registry_columns())
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry.to_dict())
