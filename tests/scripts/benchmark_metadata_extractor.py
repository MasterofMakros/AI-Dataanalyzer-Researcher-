#!/usr/bin/env python3
"""Benchmark metadata extractor API latency for sample files."""

import json
import os
import sys
import time
from pathlib import Path
from uuid import uuid4
import http.client
from urllib.parse import urlparse

SAMPLES = [
    ("RAW", Path("tests/fixtures/metadata_samples/sample.raw")),
    ("PSD", Path("tests/fixtures/metadata_samples/sample.psd")),
    ("EXE", Path("tests/fixtures/metadata_samples/sample.exe")),
]

ENDPOINT = os.getenv("METADATA_EXTRACTOR_URL", "http://localhost:8015/metadata")
OUTPUT = Path(os.getenv("METADATA_BENCH_OUTPUT", "tests/scripts/benchmark_metadata_results.json"))


def _build_multipart(file_path: Path) -> tuple[bytes, str]:
    boundary = f"----metadata-{uuid4().hex}"
    filename = file_path.name
    content = file_path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, boundary


def _post_file(url: str, file_path: Path) -> None:
    parsed = urlparse(url)
    body, boundary = _build_multipart(file_path)

    conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
    }

    conn.request("POST", parsed.path, body=body, headers=headers)
    response = conn.getresponse()
    payload = response.read()

    if response.status != 200:
        raise RuntimeError(f"HTTP {response.status}: {payload.decode('utf-8')}")


def _ensure_sample_files() -> None:
    samples_dir = Path("tests/fixtures/metadata_samples")
    samples_dir.mkdir(parents=True, exist_ok=True)

    raw_path = samples_dir / "sample.raw"
    if not raw_path.exists():
        raw_header = b"II*\x00" + (8).to_bytes(4, "little")
        raw_path.write_bytes(raw_header + b"\x00" * 1024)

    psd_path = samples_dir / "sample.psd"
    if not psd_path.exists():
        psd_header = b"8BPS"
        psd_header += (1).to_bytes(2, "big")
        psd_header += b"\x00" * 6
        psd_header += (1).to_bytes(2, "big")
        psd_header += (1).to_bytes(4, "big")
        psd_header += (1).to_bytes(4, "big")
        psd_header += (8).to_bytes(2, "big")
        psd_header += (3).to_bytes(2, "big")
        psd_path.write_bytes(psd_header + b"\x00" * 1024)

    exe_path = samples_dir / "sample.exe"
    if not exe_path.exists():
        exe_stub = b"MZ" + b"\x90" * 58 + b"\x40\x00\x00\x00"
        exe_stub += b"This program cannot be run in DOS mode.\r\n$"
        exe_path.write_bytes(exe_stub.ljust(1024, b"\x00"))


def main() -> int:
    _ensure_sample_files()
    results = []
    for label, path in SAMPLES:
        if not path.exists():
            print(f"Missing sample file: {path}")
            return 1

        start = time.perf_counter()
        _post_file(ENDPOINT, path)
        duration_ms = (time.perf_counter() - start) * 1000

        results.append({
            "file": str(path),
            "file_type": label,
            "duration_ms": round(duration_ms, 2)
        })
        print(f"{label}: {duration_ms:.2f} ms")

    payload = {
        "run_id": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": ENDPOINT,
        "samples": results,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote benchmark results to {OUTPUT}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
