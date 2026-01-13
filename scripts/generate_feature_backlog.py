#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys


ALLOWED_PRP_STATUSES = {"planned", "in-progress", "blocked"}


def parse_feature_table(project_status_text: str) -> list[dict[str, str]]:
    lines = project_status_text.splitlines()
    header_index = None
    header_pattern = re.compile(
        r"^\|\s*ID\s*\|\s*Feature\s*\|\s*Status\s*\|\s*PRP-Link\s*\|\s*Abhängigkeiten\s*\|\s*Validierung\s*\|\s*$"
    )
    for idx, line in enumerate(lines):
        if header_pattern.match(line):
            header_index = idx
            break
    if header_index is None:
        return []

    entries: list[dict[str, str]] = []
    for line in lines[header_index + 2 :]:
        if not line.strip().startswith("|"):
            break
        columns = [col.strip() for col in line.strip().strip("|").split("|")]
        if len(columns) < 6:
            continue
        entries.append(
            {
                "id": columns[0],
                "feature": columns[1],
                "status": columns[2],
                "prp_link": columns[3],
                "dependencies": columns[4],
                "validation": columns[5],
            }
        )
    return entries


def collect_prp_statuses(prp_root: Path) -> dict[Path, str]:
    statuses: dict[Path, str] = {}
    for path in prp_root.glob("*.md"):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        status_match = re.search(r"^Status:\s*(.+)$", text, re.MULTILINE)
        if status_match:
            statuses[path.resolve()] = status_match.group(1).strip().lower()
    return statuses


def build_backlog_rows(
    feature_rows: list[dict[str, str]],
    prp_statuses: dict[Path, str],
    project_status_dir: Path,
) -> list[dict[str, str]]:
    backlog_rows: list[dict[str, str]] = []
    for row in feature_rows:
        status = row["status"].strip().lower()
        if status == "done":
            continue
        prp_link = row["prp_link"].strip()
        prp_path = (project_status_dir / prp_link).resolve() if prp_link else None
        prp_status = prp_statuses.get(prp_path)
        if prp_status not in ALLOWED_PRP_STATUSES:
            if prp_path:
                print(
                    f"Skipping {row['id']} - PRP status '{prp_status}' not in {sorted(ALLOWED_PRP_STATUSES)}",
                    file=sys.stderr,
                )
            else:
                print(
                    f"Skipping {row['id']} - missing PRP link",
                    file=sys.stderr,
                )
            continue
        backlog_rows.append(row)
    return backlog_rows


def render_backlog(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Feature Backlog",
        "",
        "> Hinweis: Quelle der Wahrheit ist `docs/PROJECT_STATUS.md`. Änderungen bitte dort durchführen.",
        "",
        "| ID | Feature | Status | PRP-Link | Abhängigkeiten | Validierung |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {feature} | {status} | {prp_link} | {dependencies} | {validation} |".format(
                **row
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    project_status_path = repo_root / "docs" / "PROJECT_STATUS.md"
    backlog_path = repo_root / "docs" / "FEATURE_BACKLOG.md"
    prp_root = repo_root / "PRPs"

    project_status_text = project_status_path.read_text(encoding="utf-8")
    feature_rows = parse_feature_table(project_status_text)
    if not feature_rows:
        print("No feature table found in docs/PROJECT_STATUS.md", file=sys.stderr)
        return 1

    prp_statuses = collect_prp_statuses(prp_root)
    backlog_rows = build_backlog_rows(feature_rows, prp_statuses, project_status_path.parent)

    backlog_path.write_text(render_backlog(backlog_rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
