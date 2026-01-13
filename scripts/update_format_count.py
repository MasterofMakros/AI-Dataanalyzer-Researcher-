#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "docs" / "capabilities" / "formats.md"
README_PATH = ROOT / "README.md"


def load_format_count(source_path: Path) -> str:
    source_text = source_path.read_text(encoding="utf-8")
    match = re.search(r"Aktuelle Formatanzahl:\\s*(\\d+\\+)", source_text)
    if not match:
        raise ValueError(
            f"Keine Formatanzahl in {source_path} gefunden. "
            "Erwartet: 'Aktuelle Formatanzahl: <Zahl>+'."
        )
    return match.group(1)


def update_readme(readme_path: Path, format_count: str) -> int:
    readme_text = readme_path.read_text(encoding="utf-8")
    updated_text, replacements = re.subn(
        r"\\d+\\+\\s+Dateiformate",
        f"{format_count} Dateiformate",
        readme_text,
    )
    if replacements:
        readme_path.write_text(updated_text, encoding="utf-8")
    return replacements


def main() -> int:
    format_count = load_format_count(SOURCE_PATH)
    replacements = update_readme(README_PATH, format_count)
    if replacements == 0:
        print("Keine README-Ersetzungen vorgenommen (Muster nicht gefunden).")
    else:
        print(f"README aktualisiert: {replacements} Ersetzungen.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        raise SystemExit(1)
