#!/usr/bin/env python3
"""Compare docker-compose port mappings against docs/architecture/service-matrix.md."""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
DOCS_MATRIX = ROOT / "docs" / "architecture" / "service-matrix.md"
COMPOSE_FILES = [
    ROOT / "docker-compose.yml",
    ROOT / "docker-compose.intelligence.yml",
    ROOT / "docker-compose.prod.yml",
]

PORT_PATTERN = re.compile(r"^(?P<host>\d+):(?P<container>\d+)(?:/\w+)?$")


def extract_ports(compose_path: Path) -> dict[str, list[str]]:
    data = yaml.safe_load(compose_path.read_text()) or {}
    services = data.get("services", {})
    ports_by_service: dict[str, list[str]] = {}
    for service, config in services.items():
        ports = config.get("ports", []) if isinstance(config, dict) else []
        mappings: list[str] = []
        for entry in ports:
            if isinstance(entry, str):
                match = PORT_PATTERN.match(entry.strip())
                if match:
                    mappings.append(f"{match.group('host')} → {match.group('container')}")
            elif isinstance(entry, dict):
                published = entry.get("published")
                target = entry.get("target")
                if published and target:
                    mappings.append(f"{published} → {target}")
        if mappings:
            ports_by_service[f"{compose_path.name}:{service}"] = mappings
    return ports_by_service


def main() -> int:
    if not DOCS_MATRIX.exists():
        print("docs/architecture/service-matrix.md not found.", file=sys.stderr)
        return 1

    matrix_text = DOCS_MATRIX.read_text()

    ports_missing: list[str] = []

    for compose_path in COMPOSE_FILES:
        if not compose_path.exists():
            continue
        ports_by_service = extract_ports(compose_path)
        for service_key, mappings in ports_by_service.items():
            for mapping in mappings:
                if mapping not in matrix_text:
                    ports_missing.append(f"{service_key} -> {mapping}")

    if ports_missing:
        print("Port mappings missing in docs/architecture/service-matrix.md:")
        for item in ports_missing:
            print(f"  - {item}")
        return 1

    print("Service matrix ports match compose files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
