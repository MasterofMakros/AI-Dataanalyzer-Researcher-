"""
Database parser utilities for MDB/ACCDB/DBF/SQLite formats.
"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
import subprocess
from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from dbfread import DBF


SUPPORTED_EXTENSIONS = {
    ".sqlite",
    ".sqlite3",
    ".db",
    ".db3",
    ".dbf",
    ".mdb",
    ".accdb",
}


@dataclass
class ColumnInfo:
    name: str
    type: str
    nullable: Optional[bool] = None
    primary_key: Optional[bool] = None


@dataclass
class TableSchema:
    name: str
    columns: List[ColumnInfo]
    row_count: Optional[int] = None
    preview: Optional[List[Dict[str, object]]] = None


def detect_format(path: Path) -> str:
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported database extension: {ext}")
    if ext in {".db", ".db3", ".sqlite", ".sqlite3"}:
        return "sqlite"
    if ext == ".dbf":
        return "dbf"
    return "mdb"


def sqlite_list_tables(conn: sqlite3.Connection) -> List[str]:
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]


def sqlite_table_schema(conn: sqlite3.Connection, table: str) -> List[ColumnInfo]:
    cursor = conn.execute(f"PRAGMA table_info({quote_sqlite_identifier(table)})")
    columns = []
    for cid, name, col_type, notnull, default, pk in cursor.fetchall():
        columns.append(
            ColumnInfo(
                name=name,
                type=col_type or "",
                nullable=not bool(notnull),
                primary_key=bool(pk),
            )
        )
    return columns


def sqlite_row_count(conn: sqlite3.Connection, table: str) -> int:
    cursor = conn.execute(f"SELECT COUNT(*) FROM {quote_sqlite_identifier(table)}")
    return int(cursor.fetchone()[0])


def sqlite_preview(conn: sqlite3.Connection, table: str, limit: int) -> List[Dict[str, object]]:
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        f"SELECT * FROM {quote_sqlite_identifier(table)} LIMIT ?",
        (limit,),
    )
    return [dict(row) for row in cursor.fetchall()]


def sqlite_export(conn: sqlite3.Connection, table: str, limit: Optional[int]) -> List[Dict[str, object]]:
    conn.row_factory = sqlite3.Row
    if limit is None:
        cursor = conn.execute(f"SELECT * FROM {quote_sqlite_identifier(table)}")
    else:
        cursor = conn.execute(
            f"SELECT * FROM {quote_sqlite_identifier(table)} LIMIT ?",
            (limit,),
        )
    return [dict(row) for row in cursor.fetchall()]


def dbf_table_schema(dbf_path: Path) -> List[ColumnInfo]:
    table = DBF(str(dbf_path), load=False, ignore_missing_memofile=True)
    columns = []
    for field in table.fields:
        columns.append(ColumnInfo(name=field.name, type=field.type))
    return columns


def dbf_row_count(dbf_path: Path) -> int:
    table = DBF(str(dbf_path), load=False, ignore_missing_memofile=True)
    return len(table)


def dbf_preview(dbf_path: Path, limit: int) -> List[Dict[str, object]]:
    table = DBF(str(dbf_path), load=False, ignore_missing_memofile=True)
    return [dict(record) for record in islice(table, limit)]


def dbf_export(dbf_path: Path, limit: Optional[int]) -> List[Dict[str, object]]:
    table = DBF(str(dbf_path), load=False, ignore_missing_memofile=True)
    iterator: Iterable[Dict[str, object]]
    if limit is None:
        iterator = (dict(record) for record in table)
    else:
        iterator = (dict(record) for record in islice(table, limit))
    return list(iterator)


def mdb_tables(path: Path) -> List[str]:
    result = subprocess.run(
        ["mdb-tables", "-1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    tables = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return [table for table in tables if not table.lower().startswith("msys")]


def mdb_schema(path: Path, table: str) -> List[ColumnInfo]:
    result = subprocess.run(
        ["mdb-schema", str(path), "-T", table],
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_mdb_schema_output(result.stdout, table)


def parse_mdb_schema_output(schema_sql: str, table: str) -> List[ColumnInfo]:
    columns: List[ColumnInfo] = []
    capture = False
    for line in schema_sql.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("create table") and table.lower() in stripped.lower():
            capture = True
            continue
        if capture:
            if stripped.startswith(");"):
                break
            if not stripped or stripped.startswith("--"):
                continue
            column_line = stripped.rstrip(",")
            if column_line.lower().startswith("constraint"):
                continue
            parts = column_line.split()
            if not parts:
                continue
            name = parts[0].strip('"')
            col_type = " ".join(parts[1:])
            columns.append(ColumnInfo(name=name, type=col_type))
    return columns


def mdb_export_rows(path: Path, table: str, limit: Optional[int]) -> List[Dict[str, object]]:
    result = subprocess.run(
        ["mdb-export", "-H", str(path), table],
        check=True,
        capture_output=True,
        text=True,
    )
    reader = csv.DictReader(io.StringIO(result.stdout))
    rows = []
    for row in reader:
        rows.append(row)
        if limit is not None and len(rows) >= limit:
            break
    return rows


def mdb_row_count(path: Path, table: str) -> int:
    result = subprocess.run(
        ["mdb-export", "-H", str(path), table],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return 0
    return max(len(lines) - 1, 0)


def quote_sqlite_identifier(identifier: str) -> str:
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


def build_schema(path: Path, sample_rows: int = 5, include_row_counts: bool = True) -> Dict[str, object]:
    fmt = detect_format(path)
    tables: List[TableSchema] = []

    if fmt == "sqlite":
        conn = sqlite3.connect(path)
        try:
            for table in sqlite_list_tables(conn):
                columns = sqlite_table_schema(conn, table)
                row_count = sqlite_row_count(conn, table) if include_row_counts else None
                preview = sqlite_preview(conn, table, sample_rows) if sample_rows else None
                tables.append(
                    TableSchema(
                        name=table,
                        columns=columns,
                        row_count=row_count,
                        preview=preview,
                    )
                )
        finally:
            conn.close()
    elif fmt == "dbf":
        table_name = path.stem
        columns = dbf_table_schema(path)
        row_count = dbf_row_count(path) if include_row_counts else None
        preview = dbf_preview(path, sample_rows) if sample_rows else None
        tables.append(
            TableSchema(
                name=table_name,
                columns=columns,
                row_count=row_count,
                preview=preview,
            )
        )
    else:
        for table in mdb_tables(path):
            columns = mdb_schema(path, table)
            row_count = mdb_row_count(path, table) if include_row_counts else None
            preview = mdb_export_rows(path, table, sample_rows) if sample_rows else None
            tables.append(
                TableSchema(
                    name=table,
                    columns=columns,
                    row_count=row_count,
                    preview=preview,
                )
            )

    return {
        "path": str(path),
        "format": fmt,
        "tables": [
            {
                "name": table.name,
                "columns": [column.__dict__ for column in table.columns],
                "row_count": table.row_count,
                "preview": table.preview,
            }
            for table in tables
        ],
    }


def export_table(
    path: Path,
    table: str,
    output_format: str,
    limit: Optional[int] = None,
) -> Dict[str, object]:
    fmt = detect_format(path)
    output_format = output_format.lower()
    if output_format not in {"csv", "jsonl"}:
        raise ValueError("output_format must be 'csv' or 'jsonl'")

    if fmt == "sqlite":
        conn = sqlite3.connect(path)
        try:
            rows = sqlite_export(conn, table, limit)
        finally:
            conn.close()
    elif fmt == "dbf":
        rows = dbf_export(path, limit)
    else:
        rows = mdb_export_rows(path, table, limit)

    if output_format == "csv":
        content = rows_to_csv(rows)
    else:
        content = rows_to_jsonl(rows)

    return {
        "path": str(path),
        "format": fmt,
        "table": table,
        "row_count": len(rows),
        "content": content,
    }


def rows_to_csv(rows: List[Dict[str, object]]) -> str:
    output = io.StringIO()
    if not rows:
        return ""
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def rows_to_jsonl(rows: List[Dict[str, object]]) -> str:
    return "\n".join(json.dumps(row, default=str) for row in rows)
