# HKJC Quant Modeling Factory (Codex-Operated)

This repository now includes an executable **deterministic market-blended live board scorer** scaffold.

## Mission
Build a production-grade pipeline where:
- official HKJC data is the source of truth,
- calibrated statistical/ML models produce probabilities,
- market odds are blended into final estimates,
- wagers fire only when overlay thresholds are satisfied.

## What is implemented now
- Data contracts for race packets and runner inputs.
- Deterministic probability normalization and market implied-probability conversion.
- Convex market+model probability blending.
- Live-board scorer producing fair odds, expected value, and overlay flags.
- Unit tests for probability math and live-board execution.

## Repository pointers
- [`src/hkjc_factory/contracts.py`](src/hkjc_factory/contracts.py): input validation contracts.
- [`src/hkjc_factory/probability.py`](src/hkjc_factory/probability.py): probability, blend, and overlay logic.
- [`src/hkjc_factory/live_board.py`](src/hkjc_factory/live_board.py): CLI entry point for race packet scoring.
- [`configs/sample_race_packet.json`](configs/sample_race_packet.json): sample deterministic input.
- [`configs/betting_policy.example.json`](configs/betting_policy.example.json): example policy parameters.

## Quickstart
```bash
python -m unittest discover -s tests -v
PYTHONPATH=src python -m hkjc_factory.live_board configs/sample_race_packet.json --market-weight 0.55 --overlay-threshold 0.03
```

## Core principles
1. Never invent race data.
2. Missing values stay missing.
3. Probabilities are optimized before ROI.
4. Market blend is mandatory.
5. Every change must be reproducible and test-covered.
