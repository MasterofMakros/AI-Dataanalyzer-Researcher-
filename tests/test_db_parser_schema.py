"""
Tests for DB parser schema + preview using sample databases.
"""

import base64
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PARSER_PATH = REPO_ROOT / "infra" / "docker" / "db-parser"
sys.path.append(str(DB_PARSER_PATH))

from db_parser import build_schema  # noqa: E402


DBF_SAMPLE_BASE64 = (
    "A34BDAMAAACBAEEAAAAAAAAAAAAAAAAAAAAAAAAAAABJRAAAAAAAAAAAAE4BAAAABAAAAAAAAAAA"
    "AAAAAAAAAE5BTUUAAAAAAAAAQwUAAAAoAAAAAAAAAAAAAAAAAAAAUkVHSU9OAAAAAABDLQAAABQA"
    "AAAAAAAAAAAAAAAAAAANICAgIDFFZHNnZXIgRGlqa3N0cmEgICAgICAgICAgICAgICAgICAgICAg"
    "ICAgUm90dGVyZGFtICAgICAgICAgICAgICAgMkRvbmFsZCBLbnV0aCAgICAgICAgICAgICAgICAg"
    "ICAgICAgICAgICBNaWx3YXVrZWUgICAgICAgICAgICAgICAzQmFyYmFyYSBMaXNrb3YgICAgICAg"
    "ICAgICAgICAgICAgICAgICAgIExvcyBBbmdlbGVzICAgICAgICAgGg=="
)


def create_sqlite_sample(tmp_path: Path) -> Path:
    sqlite_path = tmp_path / "sample.sqlite"
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, city TEXT)")
    cur.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, total REAL)")
    cur.executemany(
        "INSERT INTO customers (id, name, city) VALUES (?, ?, ?)",
        [
            (1, "Ada Lovelace", "London"),
            (2, "Grace Hopper", "New York"),
            (3, "Alan Turing", "Manchester"),
        ],
    )
    cur.executemany(
        "INSERT INTO orders (id, customer_id, total) VALUES (?, ?, ?)",
        [
            (101, 1, 120.50),
            (102, 2, 230.00),
            (103, 1, 75.25),
        ],
    )
    conn.commit()
    conn.close()
    return sqlite_path


def create_dbf_sample(tmp_path: Path) -> Path:
    dbf_path = tmp_path / "sample.dbf"
    dbf_path.write_bytes(base64.b64decode(DBF_SAMPLE_BASE64))
    return dbf_path


@pytest.mark.parametrize("sample_key", ["sqlite", "dbf"])
def test_schema_row_counts_and_preview(sample_key):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        if sample_key == "sqlite":
            path = create_sqlite_sample(tmp_path)
            expected_tables = {"customers": 3, "orders": 3}
        else:
            path = create_dbf_sample(tmp_path)
            expected_tables = {"sample": 3}

        schema = build_schema(path, sample_rows=2, include_row_counts=True)
        assert schema["path"].endswith(path.name)
        table_map = {table["name"]: table for table in schema["tables"]}

        for table_name, expected_rows in expected_tables.items():
            assert table_name in table_map
            table = table_map[table_name]
            assert table["row_count"] == expected_rows
            assert table["preview"] is not None
            assert len(table["preview"]) == 2
