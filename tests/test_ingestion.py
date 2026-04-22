import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hkjc_factory.ingestion.id_mapper import build_race_id, build_runner_id
from hkjc_factory.ingestion.parsers import parse_odds_snapshot, parse_race_card
from hkjc_factory.ingestion.quality import (
    check_packet_completeness,
    check_snapshot_freshness_seconds,
)


class IngestionTests(unittest.TestCase):
    def test_deterministic_ids(self):
        r1 = build_race_id("2026-04-22", "ST", 5)
        r2 = build_race_id("2026-04-22", "ST", 5)
        self.assertEqual(r1, r2)

        run1 = build_runner_id(r1, "H001", 1)
        run2 = build_runner_id(r1, "H001", 1)
        self.assertEqual(run1, run2)

    def test_parse_race_card(self):
        source = json.loads((ROOT / "tests/fixtures/race_card_source.json").read_text())
        packet = parse_race_card(source)
        self.assertTrue(packet["race_id"].startswith("RACE-"))
        self.assertEqual(len(packet["runners"]), 5)

        ok, errors = check_packet_completeness(packet)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_parse_odds_snapshot(self):
        source = json.loads((ROOT / "tests/fixtures/odds_snapshot_source.json").read_text())
        out = parse_odds_snapshot(source)
        self.assertEqual(len(out["odds"]), 2)
        self.assertEqual(out["odds"][0]["runner_id"], "RUN-1")

    def test_freshness_check(self):
        ts = (datetime.now(timezone.utc) - timedelta(seconds=50)).isoformat()
        self.assertTrue(check_snapshot_freshness_seconds(ts, max_age_seconds=120))
        self.assertFalse(check_snapshot_freshness_seconds(ts, max_age_seconds=10))


if __name__ == "__main__":
    unittest.main()
