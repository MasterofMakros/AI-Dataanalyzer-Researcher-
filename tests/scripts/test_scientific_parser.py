"""Smoke test for scientific parser extractors."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_extractors(repo_root: Path):
    extractor_path = repo_root / "infra" / "docker" / "scientific-parser" / "scientific_extractors.py"
    spec = importlib.util.spec_from_file_location("scientific_extractors", extractor_path)
    module = importlib.util.module_from_spec(spec)
    if spec and spec.loader:
        spec.loader.exec_module(module)
    return module


def _assert_table(table: dict, expected_rows: int, expected_columns: list[str]):
    assert table["row_count"] == expected_rows
    assert table["column_count"] == len(expected_columns)
    assert table["columns"] == expected_columns


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    samples_dir = repo_root / "data" / "samples" / "scientific"
    extractors = _load_extractors(repo_root)

    csv_result = extractors.extract_scientific_file(samples_dir / "sample_table.csv")
    assert csv_result["table_count"] == 1
    _assert_table(csv_result["tables"][0], 3, ["id", "value", "score"])

    tsv_result = extractors.extract_scientific_file(samples_dir / "sample_table.tsv")
    assert tsv_result["table_count"] == 1
    _assert_table(tsv_result["tables"][0], 2, ["id", "value", "score"])

    json_result = extractors.extract_scientific_file(samples_dir / "sample_table.json")
    assert json_result["table_count"] == 1
    _assert_table(json_result["tables"][0], 2, ["id", "value", "score"])

    text_result = extractors.extract_scientific_file(samples_dir / "sample_text.tex")
    assert text_result["table_count"] == 0
    assert "Scientific parser smoke test" in text_result["text"]

    print("Scientific parser extractor tests passed.")


if __name__ == "__main__":
    main()
