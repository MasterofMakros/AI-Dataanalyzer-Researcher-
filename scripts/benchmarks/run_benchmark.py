#!/usr/bin/env python3
"""Benchmark harness stub for Hybrid vs Dense search.

Usage:
  python scripts/benchmarks/run_benchmark.py \
    --query-set docs/benchmarks/query_set_template.jsonl \
    --mode dense
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class QueryCase:
    id: str
    modality: str
    query: str
    expected_ids: List[str]
    notes: str | None = None


def load_queries(path: Path) -> List[QueryCase]:
    cases: List[QueryCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        cases.append(
            QueryCase(
                id=payload["id"],
                modality=payload["modality"],
                query=payload["query"],
                expected_ids=payload.get("expected_ids", []),
                notes=payload.get("notes"),
            )
        )
    return cases


def measure_latency(cases: Iterable[QueryCase]) -> float:
    start = time.perf_counter()
    # Placeholder for actual calls to Conductor API.
    for _case in cases:
        time.sleep(0.001)
    return (time.perf_counter() - start) * 1000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query-set", type=Path, required=True)
    parser.add_argument("--mode", choices=["dense", "hybrid"], default="dense")
    args = parser.parse_args()

    cases = load_queries(args.query_set)
    latency_ms = measure_latency(cases)

    print("Benchmark summary")
    print(f"Mode: {args.mode}")
    print(f"Queries: {len(cases)}")
    print(f"Total latency (ms): {latency_ms:.2f}")


if __name__ == "__main__":
    main()
