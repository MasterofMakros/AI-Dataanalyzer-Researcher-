"""
Verify Ledger Update
Checks if the Batch Processor is correctly updating the SQLite DB.
"""
import sqlite3
import pandas as pd
from tabulate import tabulate

from config.paths import BASE_DIR, LEDGER_DB_PATH

DB_PATH = BASE_DIR / "ledger.db"

def check_ledger():
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Check counts
        stats = pd.read_sql_query("""
            SELECT ingest_status, COUNT(*) as count 
            FROM filesystem_entry 
            WHERE extension='.pdf' 
            GROUP BY ingest_status
        """, conn)
        
        print("\n--- Processing Status ---")
        print(tabulate(stats, headers='keys', tablefmt='psql'))
        
        # Check sample data (Shadow Ledger)
        print("\n--- Sample Processed Data (Shadow Ledger) ---")
        # Connect to Shadow Ledger
        conn2 = sqlite3.connect(LEDGER_DB_PATH)
        sample = pd.read_sql_query("""
            SELECT substr(original_filename, 1, 30) as filename, length(extracted_text) as text_len, confidence, status 
            FROM files 
            ORDER BY updated_at DESC 
            LIMIT 10
        """, conn2)
        print(tabulate(sample, headers='keys', tablefmt='psql'))
        conn2.close()
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ledger()
