"""
Triage Report Generator
Phase 3: Analyzing the 1.1M File Inventory
"""

import sqlite3
import pandas as pd
from tabulate import tabulate

from config.paths import LEDGER_DB_PATH

DB_PATH = str(LEDGER_DB_PATH)

def generate_report():
    print(f"Connecting to Ledger: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Overall Stats
    total = conn.execute("SELECT COUNT(*) FROM filesystem_entry").fetchone()[0]
    discovered = conn.execute("SELECT COUNT(*) FROM filesystem_entry WHERE status='DISCOVERED'").fetchone()[0] # Should be 0 if triage worked
    ready = conn.execute("SELECT COUNT(*) FROM filesystem_entry WHERE status='READY_FOR_INGEST'").fetchone()[0]
    ignored = conn.execute("SELECT COUNT(*) FROM filesystem_entry WHERE status='IGNORED'").fetchone()[0]
    
    print(f"\n--- Ledger Summary ---")
    print(f"Total Files: {total}")
    print(f"Ready for Ingest: {ready} ({ready/total*100:.1f}%)")
    print(f"Ignored (Noise): {ignored} ({ignored/total*100:.1f}%)")
    
    # 2. Asset Breakdown (Extension)
    print(f"\n--- Knowledge Assets (Top 20) ---")
    query = """
        SELECT extension, COUNT(*) as count, SUM(size_bytes)/1024/1024 as size_mb 
        FROM filesystem_entry 
        WHERE status='READY_FOR_INGEST'
        GROUP BY extension
        ORDER BY count DESC
        LIMIT 20
    """
    df = pd.read_sql_query(query, conn)
    print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
    
    # 3. Ignored Breakdown (for verification)
    print(f"\n--- Top Ignored Extensions (Noise check) ---")
    query_ignored = """
        SELECT extension, COUNT(*) as count 
        FROM filesystem_entry 
        WHERE status='IGNORED'
        GROUP BY extension
        ORDER BY count DESC
        LIMIT 10
    """
    df_ignored = pd.read_sql_query(query_ignored, conn)
    print(tabulate(df_ignored, headers='keys', tablefmt='psql', showindex=False))

    conn.close()

if __name__ == "__main__":
    generate_report()
