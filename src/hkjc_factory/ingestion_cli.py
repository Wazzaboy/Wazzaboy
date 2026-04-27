"""CLI to transform source race-card JSON into canonical race packet JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ingestion.parsers import parse_race_card
from .ingestion.quality import check_packet_completeness


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform race-card payload into canonical packet")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    source_payload = json.loads(args.input.read_text())
    packet = parse_race_card(source_payload)
    ok, errors = check_packet_completeness(packet)
    if not ok:
        raise ValueError("packet completeness failed: " + "; ".join(errors))

    args.output.write_text(json.dumps(packet, indent=2))
    print(f"Wrote canonical packet: {args.output}")


if __name__ == "__main__":
    main()
