"""
A/B-Test: Analytics Database
SQLite (A) vs DuckDB (B)

Messkriterien:
- Write Speed (Rows/s)
- Query Speed (Queries/s)
- Aggregation Speed
- Memory Usage (MB)
"""

import time
import os
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
import psutil
import random
import string

from config.paths import BASE_DIR

@dataclass
class DBResult:
    name: str
    write_rows_per_sec: float
    query_rows_per_sec: float
    aggregation_time_sec: float
    memory_mb: float
    db_size_mb: float


def measure_resources() -> tuple:
    """Misst aktuelle Ressourcen."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024, process.cpu_percent()


def generate_test_data(n_rows: int) -> List[tuple]:
    """Generiert Testdaten für Benchmark."""
    data = []
    for i in range(n_rows):
        data.append((
            i,
            f"file_{i}.{''.join(random.choices(string.ascii_lowercase, k=3))}",
            f"{BASE_DIR}/test/path/{i % 100}/{i % 1000}/",
            random.randint(100, 10_000_000),  # filesize
            random.choice(["pdf", "docx", "jpg", "mp4", "txt"]),
            random.random(),  # confidence
            "2025-01-01 00:00:00"
        ))
    return data


def test_sqlite(test_data: List[tuple], db_path: Path) -> DBResult:
    """Test A: SQLite"""
    print(f"\n{'='*60}")
    print(f"Test A: SQLite")
    print(f"{'='*60}")
    
    if db_path.exists():
        db_path.unlink()
    
    start_mem, _ = measure_resources()
    
    # Write Test
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY,
            filename TEXT,
            filepath TEXT,
            filesize INTEGER,
            extension TEXT,
            confidence REAL,
            created_at TEXT
        )
    """)
    
    write_start = time.time()
    cursor.executemany(
        "INSERT INTO files VALUES (?, ?, ?, ?, ?, ?, ?)",
        test_data
    )
    conn.commit()
    write_time = time.time() - write_start
    
    # Query Test (SELECT ALL)
    query_start = time.time()
    for _ in range(100):
        cursor.execute("SELECT * FROM files WHERE extension = 'pdf'")
        _ = cursor.fetchall()
    query_time = time.time() - query_start
    
    # Aggregation Test
    agg_start = time.time()
    for _ in range(100):
        cursor.execute("""
            SELECT extension, COUNT(*) as cnt, SUM(filesize) as total_size, AVG(confidence) 
            FROM files 
            GROUP BY extension
        """)
        _ = cursor.fetchall()
    agg_time = time.time() - agg_start
    
    conn.close()
    
    end_mem, _ = measure_resources()
    db_size = db_path.stat().st_size / 1024 / 1024
    
    result = DBResult(
        name="SQLite",
        write_rows_per_sec=len(test_data) / write_time,
        query_rows_per_sec=len(test_data) * 100 / query_time,
        aggregation_time_sec=agg_time,
        memory_mb=end_mem - start_mem,
        db_size_mb=db_size
    )
    
    print(f"  Write:       {result.write_rows_per_sec:,.0f} Rows/s")
    print(f"  Query:       {result.query_rows_per_sec:,.0f} Rows/s")
    print(f"  Aggregation: {result.aggregation_time_sec:.3f}s (100 Queries)")
    print(f"  Memory:      {result.memory_mb:.1f} MB")
    print(f"  DB Size:     {result.db_size_mb:.2f} MB")
    
    return result


def test_duckdb(test_data: List[tuple], db_path: Path) -> DBResult:
    """Test B: DuckDB"""
    print(f"\n{'='*60}")
    print(f"Test B: DuckDB")
    print(f"{'='*60}")
    
    try:
        import duckdb
    except ImportError:
        print("  ❌ DuckDB nicht installiert")
        return DBResult("DuckDB", 0, 0, 0, 0, 0)
    
    if db_path.exists():
        db_path.unlink()
    
    start_mem, _ = measure_resources()
    
    # Write Test - DuckDB ist optimiert für bulk inserts via Python
    conn = duckdb.connect(str(db_path))
    
    conn.execute("""
        CREATE TABLE files (
            id INTEGER,
            filename VARCHAR,
            filepath VARCHAR,
            filesize BIGINT,
            extension VARCHAR,
            confidence DOUBLE,
            created_at VARCHAR
        )
    """)
    
    write_start = time.time()
    # Effiziente Batch-Inserts über SQL VALUES
    batch_size = 1000
    for i in range(0, len(test_data), batch_size):
        batch = test_data[i:i+batch_size]
        values = ", ".join([
            f"({r[0]}, '{r[1]}', '{r[2]}', {r[3]}, '{r[4]}', {r[5]}, '{r[6]}')"
            for r in batch
        ])
        conn.execute(f"INSERT INTO files VALUES {values}")
    write_time = time.time() - write_start
    
    # Query Test (SELECT with filter)
    query_start = time.time()
    for _ in range(100):
        result = conn.execute("SELECT * FROM files WHERE extension = 'pdf'").fetchall()
    query_time = time.time() - query_start
    
    # Aggregation Test
    agg_start = time.time()
    for _ in range(100):
        result = conn.execute("""
            SELECT extension, COUNT(*) as cnt, SUM(filesize) as total_size, AVG(confidence) 
            FROM files 
            GROUP BY extension
        """).fetchall()
    agg_time = time.time() - agg_start
    
    conn.close()
    
    end_mem, _ = measure_resources()
    db_size = db_path.stat().st_size / 1024 / 1024
    
    result = DBResult(
        name="DuckDB",
        write_rows_per_sec=len(test_data) / write_time,
        query_rows_per_sec=len(test_data) * 100 / query_time,
        aggregation_time_sec=agg_time,
        memory_mb=end_mem - start_mem,
        db_size_mb=db_size
    )
    
    print(f"  Write:       {result.write_rows_per_sec:,.0f} Rows/s")
    print(f"  Query:       {result.query_rows_per_sec:,.0f} Rows/s")
    print(f"  Aggregation: {result.aggregation_time_sec:.3f}s (100 Queries)")
    print(f"  Memory:      {result.memory_mb:.1f} MB")
    print(f"  DB Size:     {result.db_size_mb:.2f} MB")
    
    return result


def compare_dbs(a: DBResult, b: DBResult):
    """Vergleiche SQLite vs DuckDB."""
    print(f"\n{'='*70}")
    print(f"A/B-TEST ERGEBNIS: SQLite vs DuckDB")
    print(f"{'='*70}")
    
    print(f"\n{'Metrik':<20} {'SQLite (A)':<15} {'DuckDB (B)':<15} {'Besser':<15}")
    print("-" * 65)
    
    # Write Speed
    better = "B ✅" if b.write_rows_per_sec > a.write_rows_per_sec else "A ✅"
    print(f"{'Write (Rows/s)':<20} {a.write_rows_per_sec:>12,.0f} {b.write_rows_per_sec:>12,.0f} {better:<15}")
    
    # Query Speed
    better = "B ✅" if b.query_rows_per_sec > a.query_rows_per_sec else "A ✅"
    print(f"{'Query (Rows/s)':<20} {a.query_rows_per_sec:>12,.0f} {b.query_rows_per_sec:>12,.0f} {better:<15}")
    
    # Aggregation
    better = "B ✅" if b.aggregation_time_sec < a.aggregation_time_sec else "A ✅"
    speedup = a.aggregation_time_sec / b.aggregation_time_sec if b.aggregation_time_sec > 0 else 0
    print(f"{'Aggregation (s)':<20} {a.aggregation_time_sec:>12.3f} {b.aggregation_time_sec:>12.3f} {better} ({speedup:.1f}x)")
    
    # Memory
    better = "B ✅" if b.memory_mb <= a.memory_mb else "A ✅"
    print(f"{'Memory (MB)':<20} {a.memory_mb:>12.1f} {b.memory_mb:>12.1f} {better:<15}")
    
    # DB Size
    better = "B ✅" if b.db_size_mb <= a.db_size_mb else "A ✅"
    print(f"{'DB Size (MB)':<20} {a.db_size_mb:>12.2f} {b.db_size_mb:>12.2f} {better:<15}")
    
    print("-" * 65)
    
    # Prüfe ob DuckDB in allen Aspekten besser
    b_better_write = b.write_rows_per_sec >= a.write_rows_per_sec
    b_better_query = b.query_rows_per_sec >= a.query_rows_per_sec
    b_better_agg = b.aggregation_time_sec <= a.aggregation_time_sec
    b_better_mem = b.memory_mb <= a.memory_mb + 50  # Toleranz
    
    all_better = all([b_better_write, b_better_query, b_better_agg])
    
    if all_better:
        print(f"\n🏆 GEWINNER: DuckDB")
        print(f"✅ EMPFEHLUNG: UPGRADE zu DuckDB für Analytics")
    else:
        print(f"\n⚠️  EMPFEHLUNG: KEEP SQLite (Trade-offs vorhanden)")
        print(f"   DuckDB nicht in allen Aspekten besser")


if __name__ == "__main__":
    print("=" * 70)
    print("NEURAL VAULT - A/B-TEST: DATABASE")
    print("=" * 70)
    
    # Generiere Testdaten (100k Rows = ~1M Dateien simuliert)
    N_ROWS = 100_000
    print(f"\nGeneriere {N_ROWS:,} Testdaten...")
    test_data = generate_test_data(N_ROWS)
    
    # Temporäre DB-Pfade
    from config.paths import TEST_SUITE_DIR
    TEST_SUITE_DIR.mkdir(parents=True, exist_ok=True)
    
    sqlite_path = TEST_SUITE_DIR / "benchmark_sqlite.db"
    duckdb_path = TEST_SUITE_DIR / "benchmark_duckdb.db"
    
    # Tests
    sqlite_result = test_sqlite(test_data, sqlite_path)
    duckdb_result = test_duckdb(test_data, duckdb_path)
    
    # Vergleich
    compare_dbs(sqlite_result, duckdb_result)
    
    # Cleanup
    if sqlite_path.exists():
        sqlite_path.unlink()
    if duckdb_path.exists():
        duckdb_path.unlink()
    
    print("\n" + "=" * 70)
    print("A/B-TEST ABGESCHLOSSEN")
    print("=" * 70)
