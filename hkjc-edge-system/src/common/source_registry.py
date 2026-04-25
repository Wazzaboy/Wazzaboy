"""Source registry for HKJC-first extraction."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceDefinition:
    """Canonical source metadata used by fetch/discovery layers."""

    name: str
    priority: int
    domains: tuple[str, ...]
    source_type: str


SOURCE_REGISTRY: dict[str, SourceDefinition] = {
    "HKJC": SourceDefinition(
        name="HKJC",
        priority=1,
        domains=("racing.hkjc.com", "bet.hkjc.com", "hkjc.com"),
        source_type="official",
    ),
    "HKHORSEDB": SourceDefinition(
        name="HKHORSEDB",
        priority=2,
        domains=("hkhorsedb.com",),
        source_type="secondary",
    ),
}


def get_source(name: str) -> SourceDefinition:
    """Return canonical source definition by name."""
    key = name.strip().upper()
    if key not in SOURCE_REGISTRY:
        msg = f"Unknown source: {name}"
        raise KeyError(msg)
    return SOURCE_REGISTRY[key]


def is_primary_source(name: str) -> bool:
    """True if source is a primary truth source."""
    return get_source(name).priority == 1


def validate_source_url(source_name: str, source_url: str) -> bool:
    """Validate URL domain against registered domains for the source."""
    parsed = urlparse(source_url)
    if not parsed.netloc:
        return False
    domain = parsed.netloc.lower()
    source = get_source(source_name)
    return any(domain == d or domain.endswith(f".{d}") for d in source.domains)
