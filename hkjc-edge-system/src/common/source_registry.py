"""Source registry definitions for HKJC-first extraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import urlparse


DISCOVERY_REQUIRED_FIELDS = [
    "source_url",
    "source_name",
    "source_page_type",
    "access_status",
    "model_value",
    "leakage_risk",
    "parser_difficulty",
    "notes",
]


@dataclass(frozen=True)
class SourcePage:
    """Single discoverable source page group entry."""

    source_url: str
    source_name: str
    source_page_type: str
    access_status: str
    model_value: str
    leakage_risk: str
    parser_difficulty: str
    notes: str


@dataclass(frozen=True)
class SourceDefinition:
    """Source-level configuration and page groups."""

    name: str
    priority: int
    source_type: str
    domains: tuple[str, ...]
    pages: tuple[SourcePage, ...]


HKJC_PAGES: tuple[SourcePage, ...] = (
    SourcePage(
        source_url="https://racing.hkjc.com/racing/information/English/racing/Racecard.aspx",
        source_name="HKJC",
        source_page_type="race_card",
        access_status="unknown",
        model_value="high",
        leakage_risk="low",
        parser_difficulty="medium",
        notes="Primary pre-race runner and declaration data.",
    ),
    SourcePage(
        source_url="https://racing.hkjc.com/racing/information/English/Racing/ResultsAll.aspx",
        source_name="HKJC",
        source_page_type="results",
        access_status="unknown",
        model_value="high",
        leakage_risk="post_race_only",
        parser_difficulty="medium",
        notes="Official post-race result records.",
    ),
    SourcePage(
        source_url="https://bet.hkjc.com/racing/pages/odds_wp.aspx",
        source_name="HKJC",
        source_page_type="current_odds",
        access_status="unknown",
        model_value="high",
        leakage_risk="time_sensitive",
        parser_difficulty="high",
        notes="Public odds page; snapshot timestamp required.",
    ),
    SourcePage(
        source_url="https://racing.hkjc.com/racing/information/English/racing/ResultsDividends.aspx",
        source_name="HKJC",
        source_page_type="dividends",
        access_status="unknown",
        model_value="medium",
        leakage_risk="post_race_only",
        parser_difficulty="medium",
        notes="Official dividends; no same-race pre-race usage.",
    ),
)


HKHORSEDB_PAGES: tuple[SourcePage, ...] = (
    SourcePage(
        source_url="https://www.hkhorsedb.com",
        source_name="HKHORSEDB",
        source_page_type="site_root",
        access_status="placeholder",
        model_value="medium",
        leakage_risk="third_party",
        parser_difficulty="unknown",
        notes="Secondary enrichment only; never overrides HKJC without manual review.",
    ),
)


SOURCE_REGISTRY: dict[str, SourceDefinition] = {
    "HKJC": SourceDefinition(
        name="HKJC",
        priority=1,
        source_type="official",
        domains=("racing.hkjc.com", "bet.hkjc.com", "hkjc.com"),
        pages=HKJC_PAGES,
    ),
    "HKHORSEDB": SourceDefinition(
        name="HKHORSEDB",
        priority=2,
        source_type="secondary",
        domains=("hkhorsedb.com", "www.hkhorsedb.com"),
        pages=HKHORSEDB_PAGES,
    ),
}


def get_source(name: str) -> SourceDefinition:
    key = name.strip().upper()
    if key not in SOURCE_REGISTRY:
        raise KeyError(f"Unknown source: {name}")
    return SOURCE_REGISTRY[key]


def is_primary_source(name: str) -> bool:
    return get_source(name).priority == 1


def validate_source_url(source_name: str, source_url: str) -> bool:
    parsed = urlparse(source_url)
    if not parsed.netloc:
        return False
    source = get_source(source_name)
    domain = parsed.netloc.lower()
    return any(domain == reg or domain.endswith(f".{reg}") for reg in source.domains)


def source_pages_as_rows(source_name: str) -> list[dict[str, str]]:
    source = get_source(source_name)
    return [asdict(page) for page in source.pages]
