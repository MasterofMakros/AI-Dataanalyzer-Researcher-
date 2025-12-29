"""
A/B-Test: Hybrid Database Strategy
A: SQLite-Only (aktuell)
B: Hybrid (SQLite für Writes + DuckDB für Analytics)

Realistische Workflow-Simulation:
1. Ingest-Phase: 10k Writes
2. Analytics-Phase: Dashboard-Queries (Aggregationen)
3. Mixed-Workload: 80% Reads, 20% Writes
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
from config.paths import BASE_DIR, TEST_SUITE_DIR

@dataclass
class WorkflowResult:
    name: str
    ingest_time_sec: float
    analytics_time_sec: float
    mixed_time_sec: float
    total_time_sec: float
    memory_mb: float
    writes_per_sec: float
    queries_per_sec: float


def measure_resources() -> float:
    """Misst aktuellen RAM."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def generate_file_record():
    """Generiert einen realistischen Datei-Eintrag."""
    return (
        f"file_{random.randint(1, 999999)}.{''.join(random.choices(string.ascii_lowercase, k=3))}",
        f"{BASE_DIR}/test/path/{random.randint(1, 100)}/{random.randint(1, 1000)}/",
        random.randint(100, 10_000_000),
        random.choice(["pdf", "docx", "jpg", "mp4", "txt", "xlsx", "pptx"]),
        random.random(),
        "2025-01-01 00:00:00"
    )


def test_sqlite_only(n_ingest: int = 10000, n_analytics: int = 50, n_mixed: int = 1000) -> WorkflowResult:
    """Test A: SQLite-Only (aktuell)"""
    print(f"\n{'='*60}")
    print(f"Test A: SQLite-Only (aktueller Stand)")
    print(f"{'='*60}")
    
    db_path = Path("F:/_TestSuite/workflow_sqlite.db")
    if db_path.exists():
        db_path.unlink()
    
    start_mem = measure_resources()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            filepath TEXT,
            filesize INTEGER,
            extension TEXT,
            confidence REAL,
            created_at TEXT
        )
    """)
    cursor.execute("CREATE INDEX idx_ext ON files(extension)")
    conn.commit()
    
    # Phase 1: Ingest (Write-Heavy)
    print(f"  [1/3] Ingest: {n_ingest:,} Dateien...")
    ingest_start = time.time()
    for _ in range(n_ingest):
        record = generate_file_record()
        cursor.execute(
            "INSERT INTO files (filename, filepath, filesize, extension, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            record
        )
    conn.commit()
    ingest_time = time.time() - ingest_start
    print(f"      → {ingest_time:.2f}s ({n_ingest/ingest_time:,.0f} Writes/s)")
    
    # Phase 2: Analytics (Dashboard-Queries)
    print(f"  [2/3] Analytics: {n_analytics} Dashboard-Queries...")
    analytics_start = time.time()
    for _ in range(n_analytics):
        # Typische Dashboard-Abfragen
        cursor.execute("SELECT extension, COUNT(*), SUM(filesize), AVG(confidence) FROM files GROUP BY extension")
        _ = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM files WHERE confidence > 0.8")
        _ = cursor.fetchone()
        cursor.execute("SELECT extension, COUNT(*) FROM files GROUP BY extension ORDER BY COUNT(*) DESC LIMIT 5")
        _ = cursor.fetchall()
    analytics_time = time.time() - analytics_start
    print(f"      → {analytics_time:.2f}s ({n_analytics*3/analytics_time:,.0f} Queries/s)")
    
    # Phase 3: Mixed Workload (80% Reads, 20% Writes)
    print(f"  [3/3] Mixed: {n_mixed} Operationen (80/20)...")
    mixed_start = time.time()
    for i in range(n_mixed):
        if random.random() < 0.8:
            # Read
            cursor.execute("SELECT * FROM files WHERE extension = ?", (random.choice(["pdf", "jpg", "mp4"]),))
            _ = cursor.fetchall()
        else:
            # Write
            record = generate_file_record()
            cursor.execute(
                "INSERT INTO files (filename, filepath, filesize, extension, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                record
            )
    conn.commit()
    mixed_time = time.time() - mixed_start
    print(f"      → {mixed_time:.2f}s ({n_mixed/mixed_time:,.0f} Ops/s)")
    
    conn.close()
    if db_path.exists():
        db_path.unlink()
    
    total_time = ingest_time + analytics_time + mixed_time
    end_mem = measure_resources()
    
    return WorkflowResult(
        name="SQLite-Only",
        ingest_time_sec=ingest_time,
        analytics_time_sec=analytics_time,
        mixed_time_sec=mixed_time,
        total_time_sec=total_time,
        memory_mb=end_mem - start_mem,
        writes_per_sec=n_ingest / ingest_time,
        queries_per_sec=(n_analytics * 3) / analytics_time
    )


def test_hybrid(n_ingest: int = 10000, n_analytics: int = 50, n_mixed: int = 1000) -> WorkflowResult:
    """Test B: Hybrid (SQLite Writes + DuckDB Analytics)"""
    print(f"\n{'='*60}")
    print(f"Test B: Hybrid (SQLite + DuckDB)")
    print(f"{'='*60}")
    
    try:
        import duckdb
    except ImportError:
        print("  ❌ DuckDB nicht installiert")
        return WorkflowResult("Hybrid", 0, 0, 0, 0, 0, 0, 0)
    
    sqlite_path = TEST_SUITE_DIR / "workflow_hybrid_sqlite.db"
    duckdb_path = TEST_SUITE_DIR / "workflow_hybrid_duck.db"
    
    for p in [sqlite_path, duckdb_path]:
        if p.exists():
            p.unlink()
    
    start_mem = measure_resources()
    
    # SQLite für Writes
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cur = sqlite_conn.cursor()
    
    sqlite_cur.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            filepath TEXT,
            filesize INTEGER,
            extension TEXT,
            confidence REAL,
            created_at TEXT
        )
    """)
    sqlite_cur.execute("CREATE INDEX idx_ext ON files(extension)")
    sqlite_conn.commit()
    
    # Phase 1: Ingest (SQLite für Writes)
    print(f"  [1/3] Ingest: {n_ingest:,} Dateien (SQLite)...")
    ingest_start = time.time()
    for _ in range(n_ingest):
        record = generate_file_record()
        sqlite_cur.execute(
            "INSERT INTO files (filename, filepath, filesize, extension, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            record
        )
    sqlite_conn.commit()
    ingest_time = time.time() - ingest_start
    print(f"      → {ingest_time:.2f}s ({n_ingest/ingest_time:,.0f} Writes/s)")
    
    # Sync zu DuckDB für Analytics
    print(f"      Sync zu DuckDB...")
    sync_start = time.time()
    duck_conn = duckdb.connect(str(duckdb_path))
    duck_conn.execute(f"ATTACH '{sqlite_path}' AS sqlite_db (TYPE SQLITE)")
    duck_conn.execute("CREATE TABLE files AS SELECT * FROM sqlite_db.files")
    sync_time = time.time() - sync_start
    print(f"      → Sync: {sync_time:.2f}s")
    
    # Phase 2: Analytics (DuckDB)
    print(f"  [2/3] Analytics: {n_analytics} Dashboard-Queries (DuckDB)...")
    analytics_start = time.time()
    for _ in range(n_analytics):
        duck_conn.execute("SELECT extension, COUNT(*), SUM(filesize), AVG(confidence) FROM files GROUP BY extension").fetchall()
        duck_conn.execute("SELECT COUNT(*) FROM files WHERE confidence > 0.8").fetchone()
        duck_conn.execute("SELECT extension, COUNT(*) FROM files GROUP BY extension ORDER BY COUNT(*) DESC LIMIT 5").fetchall()
    analytics_time = time.time() - analytics_start
    print(f"      → {analytics_time:.2f}s ({n_analytics*3/analytics_time:,.0f} Queries/s)")
    
    # Phase 3: Mixed Workload (SQLite für Writes, DuckDB für Reads)
    print(f"  [3/3] Mixed: {n_mixed} Ops (SQLite Write, DuckDB Read)...")
    mixed_start = time.time()
    for i in range(n_mixed):
        if random.random() < 0.8:
            # Read (DuckDB)
            duck_conn.execute("SELECT * FROM files WHERE extension = ?", [random.choice(["pdf", "jpg", "mp4"])]).fetchall()
        else:
            # Write (SQLite)
            record = generate_file_record()
            sqlite_cur.execute(
                "INSERT INTO files (filename, filepath, filesize, extension, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                record
            )
    sqlite_conn.commit()
    mixed_time = time.time() - mixed_start
    print(f"      → {mixed_time:.2f}s ({n_mixed/mixed_time:,.0f} Ops/s)")
    
    sqlite_conn.close()
    duck_conn.close()
    
    for p in [sqlite_path, duckdb_path]:
        if p.exists():
            p.unlink()
    
    total_time = ingest_time + sync_time + analytics_time + mixed_time
    end_mem = measure_resources()
    
    return WorkflowResult(
        name="Hybrid",
        ingest_time_sec=ingest_time + sync_time,  # Inkl. Sync-Overhead
        analytics_time_sec=analytics_time,
        mixed_time_sec=mixed_time,
        total_time_sec=total_time,
        memory_mb=end_mem - start_mem,
        writes_per_sec=n_ingest / ingest_time,
        queries_per_sec=(n_analytics * 3) / analytics_time
    )


def compare_workflows(a: WorkflowResult, b: WorkflowResult):
    """Vergleiche die Workflows."""
    print(f"\n{'='*70}")
    print(f"A/B-TEST: SQLite-Only vs Hybrid")
    print(f"{'='*70}")
    
    print(f"\n{'Phase':<20} {'SQLite-Only':<15} {'Hybrid':<15} {'Besser':<15}")
    print("-" * 65)
    
    # Ingest
    better = "B ✅" if b.ingest_time_sec < a.ingest_time_sec else "A ✅"
    print(f"{'Ingest (s)':<20} {a.ingest_time_sec:>12.2f} {b.ingest_time_sec:>12.2f} {better}")
    
    # Analytics
    speedup = a.analytics_time_sec / b.analytics_time_sec if b.analytics_time_sec > 0 else 0
    better = f"B ✅ ({speedup:.1f}x)" if b.analytics_time_sec < a.analytics_time_sec else "A ✅"
    print(f"{'Analytics (s)':<20} {a.analytics_time_sec:>12.2f} {b.analytics_time_sec:>12.2f} {better}")
    
    # Mixed
    better = "B ✅" if b.mixed_time_sec < a.mixed_time_sec else "A ✅"
    print(f"{'Mixed (s)':<20} {a.mixed_time_sec:>12.2f} {b.mixed_time_sec:>12.2f} {better}")
    
    # Total
    speedup_total = a.total_time_sec / b.total_time_sec if b.total_time_sec > 0 else 0
    better = f"B ✅ ({speedup_total:.1f}x)" if b.total_time_sec < a.total_time_sec else "A ✅"
    print(f"{'TOTAL (s)':<20} {a.total_time_sec:>12.2f} {b.total_time_sec:>12.2f} {better}")
    
    # Memory
    better = "B ✅" if b.memory_mb <= a.memory_mb else "A ✅"
    print(f"{'Memory (MB)':<20} {a.memory_mb:>12.1f} {b.memory_mb:>12.1f} {better}")
    
    print("-" * 65)
    
    # Alle Aspekte prüfen
    b_better_total = b.total_time_sec < a.total_time_sec
    b_better_analytics = b.analytics_time_sec < a.analytics_time_sec
    b_better_ingest = b.ingest_time_sec <= a.ingest_time_sec * 1.1  # 10% Toleranz
    
    all_better = b_better_total and b_better_analytics and b_better_ingest
    
    if all_better:
        print(f"\n🏆 GEWINNER: Hybrid")
        print(f"✅ EMPFEHLUNG: UPGRADE zu Hybrid-Lösung")
    elif b_better_analytics and speedup > 2:
        print(f"\n⚠️  HYBRID: Signifikanter Analytics-Vorteil ({speedup:.1f}x)")
        print(f"   Aber Trade-off bei Ingest (Sync-Overhead)")
        print(f"   → UPGRADE nur wenn Analytics-Heavy-Workload")
    else:
        print(f"\n❌ KEIN UPGRADE: SQLite-Only ist ausreichend")


if __name__ == "__main__":
    print("=" * 70)
    print("NEURAL VAULT - A/B-TEST: WORKFLOW")
    print("Realistische Workload-Simulation")
    print("=" * 70)
    
    # Konfiguration
    N_INGEST = 10000    # Neue Dateien
    N_ANALYTICS = 50    # Dashboard-Queries
    N_MIXED = 1000      # 80% Read, 20% Write
    
    # Tests
    sqlite_result = test_sqlite_only(N_INGEST, N_ANALYTICS, N_MIXED)
    hybrid_result = test_hybrid(N_INGEST, N_ANALYTICS, N_MIXED)
    
    # Vergleich
    compare_workflows(sqlite_result, hybrid_result)
    
    print("\n" + "=" * 70)
    print("A/B-TEST ABGESCHLOSSEN")
    print("=" * 70)
