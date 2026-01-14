#!/usr/bin/env python3
"""Check for newer component versions and optionally update env pins."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional

GITHUB_API_BASE = "https://api.github.com"
REQUEST_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "conductor-component-updater",
}


@dataclass(frozen=True)
class Component:
    name: str
    repo: str
    env_key: str
    default: str


COMPONENTS: List[Component] = [
    Component(name="Apache Tika", repo="apache/tika", env_key="TIKA_TAG", default="3.2.3.0"),
    Component(name="WhisperX", repo="m-bain/whisperX", env_key="WHISPERX_VERSION", default="3.7.4"),
]


def fetch_json(url: str) -> object:
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def normalize_tag(tag: str) -> str:
    return re.sub(r"^[vV]", "", tag.strip())


def latest_github_tag(repo: str) -> Optional[str]:
    releases_url = f"{GITHUB_API_BASE}/repos/{repo}/releases/latest"
    tags_url = f"{GITHUB_API_BASE}/repos/{repo}/tags?per_page=1"

    try:
        release_data = fetch_json(releases_url)
        tag_name = release_data.get("tag_name") if isinstance(release_data, dict) else None
    except urllib.error.HTTPError as err:
        if err.code != 404:
            raise
        tag_name = None

    if not tag_name:
        tags_data = fetch_json(tags_url)
        if isinstance(tags_data, list) and tags_data:
            tag_name = tags_data[0].get("name")

    return normalize_tag(tag_name) if tag_name else None


def read_env_file(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return handle.readlines()


def parse_env(lines: List[str]) -> Dict[str, str]:
    env: Dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def update_env_lines(lines: List[str], updates: Dict[str, str]) -> List[str]:
    updated_lines: List[str] = []
    seen = set()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            updated_lines.append(line)
            continue
        key, _ = stripped.split("=", 1)
        key = key.strip()
        if key in updates:
            updated_lines.append(f"{key}={updates[key]}\n")
            seen.add(key)
        else:
            updated_lines.append(line)

    for key, value in updates.items():
        if key not in seen:
            updated_lines.append(f"{key}={value}\n")

    return updated_lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Check GitHub for newer component versions.")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Env file to read/update (default: .env).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write updated version pins to the env file.",
    )
    args = parser.parse_args()

    env_lines = read_env_file(args.env_file)
    env_values = parse_env(env_lines)

    updates: Dict[str, str] = {}
    print("Component update check:\n")

    for component in COMPONENTS:
        current = env_values.get(component.env_key, component.default)
        latest = latest_github_tag(component.repo)
        status = "unknown"
        if latest:
            status = "up-to-date" if latest == current else "update available"
        print(f"- {component.name} ({component.repo})")
        print(f"  Current: {current}")
        print(f"  Latest:  {latest or 'unavailable'}")
        print(f"  Status:  {status}\n")
        if latest and latest != current:
            updates[component.env_key] = latest

    if args.apply:
        if not env_lines:
            print(
                f"Env file '{args.env_file}' not found. Copy .env.example first, then rerun.",
                file=sys.stderr,
            )
            return 1
        if updates:
            new_lines = update_env_lines(env_lines, updates)
            with open(args.env_file, "w", encoding="utf-8") as handle:
                handle.writelines(new_lines)
            print(f"Updated {len(updates)} value(s) in {args.env_file}.")
        else:
            print("No updates to apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
