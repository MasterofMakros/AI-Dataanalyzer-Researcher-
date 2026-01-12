"""
Phase 4 Pilot Setup
Selects 5,000 random PDFs for the "Golden Dataset" run.
"""

import sqlite3
import random

from config.paths import LEDGER_DB_PATH, BASE_DIR

LEDGER_DB = LEDGER_DB_PATH

def setup_pilot():
    conn = sqlite3.connect(LEDGER_DB)
    cursor = conn.cursor()
    
    # 1. Reset Status for clean slate (optional, but good for pilot)
    # We only want to tag UNPROCESSED files or PENDING files, 
    # but to be safe we can just pick from 'indexed_passive' if we want to re-run graph,
    # OR pick 'PENDING' if we want to process new files.
    # PLAN: Pick 5000 'PENDING' files + include the 1000 already processed for a total relevant set.
    # Actually user wants "Process files... to verify phase 4".
    # Let's pick 5000 PENDING files.
    
    # Check column
    try:
        cursor.execute("SELECT pilot_batch FROM files LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE files ADD COLUMN pilot_batch INTEGER DEFAULT 0")
        conn.commit()

    print("🎲 Selecting 5,000 Candidate Files...")
    
    # Get IDs of candidates
    # We use filesystem_entry from the main ledger to find paths, 
    # but we are working on shadow_ledger 'files' table for metadata?
    # Wait, batch_processor reads from 'filesystem_entry' (Main Ledger) and writes to 'files' (Shadow).
    # We need to tag the MAIN ledger (conductor/ledger.db)
    
    MAIN_LEDGER = BASE_DIR / "ledger.db"
    conn_main = sqlite3.connect(MAIN_LEDGER)
    cursor_main = conn_main.cursor()
    
    # Check column in main ledger
    try:
        cursor_main.execute("SELECT pilot_flag FROM filesystem_entry LIMIT 1")
    except sqlite3.OperationalError:
        cursor_main.execute("ALTER TABLE filesystem_entry ADD COLUMN pilot_flag INTEGER DEFAULT 0")
        conn_main.commit()
    
    # Reset flags
    cursor_main.execute("UPDATE filesystem_entry SET pilot_flag = 0")
    conn_main.commit()
    
    # Select 5000 random PDFs
    query = "SELECT path FROM filesystem_entry WHERE extension = '.pdf' AND status = 'READY_FOR_INGEST' AND (ingest_status IS NULL OR ingest_status = 'PENDING')"
    cursor_main.execute(query)
    all_candidates = [row[0] for row in cursor_main.fetchall()]
    
    if len(all_candidates) < 5000:
        print(f"⚠️ Only {len(all_candidates)} candidates found. Using all.")
        selection = all_candidates
    else:
        selection = random.sample(all_candidates, 5000)
        
    print(f"✅ Selected {len(selection)} docs.")
    
    # Update Flags
    # Batch update is faster
    cursor_main.executemany("UPDATE filesystem_entry SET pilot_flag = 1 WHERE path = ?", [(x,) for x in selection])
    conn_main.commit()
    
    print("💾 Pilot Flag set on Main Ledger.")
    conn_main.close()
    conn.close()

if __name__ == "__main__":
    setup_pilot()
