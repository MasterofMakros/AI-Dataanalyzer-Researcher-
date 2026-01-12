"""
Phase 4 Pilot Monitor
Tracks progress of the Golden Dataset processing.
"""
import sqlite3
import time
import pandas as pd
from tabulate import tabulate
import os

from config.paths import LEDGER_DB_PATH

LEDGER_DB = LEDGER_DB_PATH

def monitor():
    while True:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            conn = sqlite3.connect(LEDGER_DB)
            
            # 1. Extraction Progress
            # Count indexed_pilot status
            res = conn.execute("SELECT COUNT(*) FROM files WHERE status='indexed_pilot'")
            count_extracted = res.fetchone()[0]
            
            # 2. Vectorization Progress
            # Count embedding_status='DONE' for pilot files
            res = conn.execute("SELECT COUNT(*) FROM files WHERE status='indexed_pilot' AND embedding_status='DONE'")
            count_vectorized = res.fetchone()[0]
            
            conn.close()
            
            print("=== 🚀 Phase 4 Pilot Monitor ===")
            print(f"Goal: 5,000 Documents")
            print("")
            print(f"📄 Text Extraction:  {count_extracted}/5000 ({count_extracted/5000*100:.1f}%)")
            print(f"🧬 Vectorization:    {count_vectorized}/5000 ({count_vectorized/5000*100:.1f}%)")
            
            if count_extracted > 0:
                print(f"   Lag: {count_extracted - count_vectorized} docs")
            
            time.sleep(5)
            
        except Exception as e:
            print(e)
            time.sleep(5)

if __name__ == "__main__":
    monitor()
