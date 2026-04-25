"""Utilities for immutable raw file archiving with content hashes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RawArchiveRecord:
    source_name: str
    source_page_type: str
    source_url: str
    extraction_timestamp: str
    content_sha256: str
    content_path: Path
    metadata_path: Path


def archive_raw_bytes(
    *,
    root_dir: Path,
    source_name: str,
    source_page_type: str,
    source_url: str,
    content: bytes,
    suffix: str = ".html",
) -> RawArchiveRecord:
    """Archive bytes as hash-addressed immutable payload and JSON metadata."""
    extraction_timestamp = datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha256(content).hexdigest()

    source_dir = root_dir / source_name.lower() / source_page_type
    source_dir.mkdir(parents=True, exist_ok=True)

    content_path = source_dir / f"{digest}{suffix}"
    metadata_path = source_dir / f"{digest}.json"

    if not content_path.exists():
        content_path.write_bytes(content)
    if not metadata_path.exists():
        metadata = {
            "source_name": source_name,
            "source_page_type": source_page_type,
            "source_url": source_url,
            "extraction_timestamp": extraction_timestamp,
            "content_sha256": digest,
            "content_file": content_path.name,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return RawArchiveRecord(
        source_name=source_name,
        source_page_type=source_page_type,
        source_url=source_url,
        extraction_timestamp=extraction_timestamp,
        content_sha256=digest,
        content_path=content_path,
        metadata_path=metadata_path,
    )
