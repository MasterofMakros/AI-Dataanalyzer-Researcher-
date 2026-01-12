"""
Scientific Parser Extractors
============================

Tabular- und Text-Extraktion für wissenschaftliche Formate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from pypdf import PdfReader

TEXT_EXTENSIONS = {".txt", ".md", ".tex", ".bib", ".ris", ".rst"}
TABULAR_EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl", ".xlsx", ".xls"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | TABULAR_EXTENSIONS | PDF_EXTENSIONS


class ScientificExtractionError(RuntimeError):
    pass


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_text_from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages_text).strip()


def _table_from_dataframe(df: pd.DataFrame, name: str, max_rows: int) -> Dict[str, Any]:
    limited = df.head(max_rows)
    records = limited.to_dict(orient="records")
    return {
        "name": name,
        "columns": list(limited.columns),
        "rows": records,
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "truncated": df.shape[0] > max_rows,
    }


def _extract_tables_from_csv(path: Path, max_rows: int) -> List[Dict[str, Any]]:
    df = pd.read_csv(path)
    return [_table_from_dataframe(df, name=path.stem, max_rows=max_rows)]


def _extract_tables_from_tsv(path: Path, max_rows: int) -> List[Dict[str, Any]]:
    df = pd.read_csv(path, sep="\t")
    return [_table_from_dataframe(df, name=path.stem, max_rows=max_rows)]


def _extract_tables_from_excel(path: Path, max_rows: int) -> List[Dict[str, Any]]:
    tables = []
    sheets = pd.read_excel(path, sheet_name=None)
    for sheet_name, df in sheets.items():
        tables.append(_table_from_dataframe(df, name=sheet_name, max_rows=max_rows))
    return tables


def _extract_tables_from_json(path: Path, max_rows: int) -> List[Dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    if isinstance(raw, list):
        df = pd.DataFrame(raw)
        return [_table_from_dataframe(df, name=path.stem, max_rows=max_rows)]
    if isinstance(raw, dict):
        if "data" in raw and isinstance(raw["data"], list):
            df = pd.DataFrame(raw["data"])
            return [_table_from_dataframe(df, name=path.stem, max_rows=max_rows)]
        df = pd.DataFrame([raw])
        return [_table_from_dataframe(df, name=path.stem, max_rows=max_rows)]
    raise ScientificExtractionError("Unsupported JSON structure for tabular extraction.")


def _extract_tables_from_jsonl(path: Path, max_rows: int) -> List[Dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    df = pd.DataFrame(rows)
    return [_table_from_dataframe(df, name=path.stem, max_rows=max_rows)]


def extract_scientific_file(path: Path, max_rows: int = 1000) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ScientificExtractionError(f"Unsupported extension: {extension}")

    text = ""
    tables: List[Dict[str, Any]] = []

    if extension in TEXT_EXTENSIONS:
        text = _read_text(path)
    elif extension in PDF_EXTENSIONS:
        text = _extract_text_from_pdf(path)
    elif extension == ".csv":
        tables = _extract_tables_from_csv(path, max_rows)
    elif extension == ".tsv":
        tables = _extract_tables_from_tsv(path, max_rows)
    elif extension in {".xlsx", ".xls"}:
        tables = _extract_tables_from_excel(path, max_rows)
    elif extension == ".json":
        tables = _extract_tables_from_json(path, max_rows)
    elif extension == ".jsonl":
        tables = _extract_tables_from_jsonl(path, max_rows)

    return {
        "filename": path.name,
        "extension": extension,
        "tables": tables,
        "table_count": len(tables),
        "text": text,
        "text_length": len(text),
    }
