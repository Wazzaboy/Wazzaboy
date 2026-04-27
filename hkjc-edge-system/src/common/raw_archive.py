from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class RawArchiveRecord:
    source_name: str
    source_url: str
    source_page_type: str
    extraction_timestamp: str
    sha256_hex: str
    content_path: str


def archive_raw_content(
    *,
    root_dir: Path,
    source_name: str,
    source_url: str,
    source_page_type: str,
    raw_bytes: bytes,
    extension: str = ".html",
) -> RawArchiveRecord:
    """Persist raw source payloads using content hashes without overwriting existing files."""
    digest = sha256(raw_bytes).hexdigest()
    source_slug = source_name.lower().replace(" ", "_")
    page_slug = source_page_type.lower().replace(" ", "_").replace("/", "_")
    day = datetime.now(UTC).strftime("%Y%m%d")

    archive_dir = root_dir / source_slug / page_slug / day
    archive_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{digest}{extension}"
    path = archive_dir / filename
    if not path.exists():
        path.write_bytes(raw_bytes)

    timestamp = datetime.now(UTC).isoformat()
    return RawArchiveRecord(
        source_name=source_name,
        source_url=source_url,
        source_page_type=source_page_type,
        extraction_timestamp=timestamp,
        sha256_hex=digest,
        content_path=str(path),
    )
