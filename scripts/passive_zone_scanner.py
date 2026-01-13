"""
Passive Zone Scanner (Periodic)
Scans the Passive Zone (F:/* excluding Inbox) and indexes new/changed files
without renaming or moving them.
"""

import sys
import os
import time
from pathlib import Path
import sqlite3

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.paths import BASE_DIR, LEDGER_DB_PATH, INBOX_DIR, QUARANTINE_DIR, ARCHIVE_DIR, TEST_SUITE_DIR
from scripts.bulk_scanner import BulkScanner
from scripts.file_indexer import process_file, generate_embedding, index_to_qdrant

# Config
SCAN_ROOT = BASE_DIR
EXCLUDED_DIRS = {
    str(INBOX_DIR), 
    str(QUARANTINE_DIR), 
    str(BASE_DIR / ".git"), 
    str(BASE_DIR / "node_modules"),
    str(BASE_DIR / "__pycache__"),
    str(BASE_DIR / "docker"), # Don't scan docker configs as user data
    str(TEST_SUITE_DIR)      # Don't scan test suite? maybe
}

def is_excluded(path: str) -> bool:
    path_obj = Path(path)
    # Check if path is inside any excluded dir
    for denied in EXCLUDED_DIRS:
        try:
            # Check if path is subpath of denied
            if Path(denied) in path_obj.parents or str(path_obj) == str(denied):
                return True
        except:
            pass
    return False

def main():
    print(f"🚀 Starting Passive Zone Scanner on {SCAN_ROOT}...")
    
    # 1. Bulk Discovery (Fast)
    scanner = BulkScanner(str(LEDGER_DB_PATH))
    # Note: BulkScanner usually scans everything. We rely on it to update 'filesystem_entry'.
    # For now, let's assume BulkScanner runs on root.
    # To avoid scanning excluded dirs effectively, BulkScanner needs filter.
    # But for MVP, we scan and filter here.
    
    # Run scanner to populate/update filesystem_entry
    print("  Running Bulk Discovery...")
    scanner.scan(str(SCAN_ROOT))
    
    # 2. Logic: Find files that are 'DISCOVERED' or 'READY_FOR_INGEST' but NOT 'INDEXED'
    # Actually, BulkScanner sets status based on extension.
    # We want to find files in filesystem_entry that are not fully processed in 'files' table?
    # Or just use the 'status' column in filesystem_entry.
    
    conn = sqlite3.connect(str(LEDGER_DB_PATH))
    # Select candidate files
    cursor = conn.execute("""
        SELECT path FROM filesystem_entry 
        WHERE status IN ('READY_FOR_INGEST', 'DISCOVERED') 
        ORDER BY modified_timestamp DESC
        LIMIT 50
    """)
    candidates = [row[0] for row in cursor.fetchall()]
    
    print(f"  Found {len(candidates)} candidates for indexing (Limit 50).")
    
    processed_count = 0
    for file_path_str in candidates:
        if is_excluded(file_path_str):
            # Mark as IGNORED
            with sqlite3.connect(str(LEDGER_DB_PATH)) as c:
                c.execute("UPDATE filesystem_entry SET status='IGNORED' WHERE path=?", (file_path_str,))
            continue
            
        path = Path(file_path_str)
        if not path.exists():
            continue
            
        print(f"  Indexing: {path.name}...")
        try:
            # Process via File Indexer logic
            # Note: process_file does NOT update DB status itself usually.
            doc = process_file(path)
            
            if doc:
                # Add status tag
                doc['passive_zone'] = True
                
                # Qdrant: Embedding + Index
                if doc.get('extracted_text'):
                    vec = generate_embedding(doc['extracted_text'])
                    if vec:
                        index_to_qdrant(doc['id'], vec, doc)
                
                # Update DB status
                status = 'INDEXED'
            else:
                status = 'FAILED'
                
        except Exception as e:
            print(f"    Error: {e}")
            status = 'ERROR'
            
        # Update Ledger
        with sqlite3.connect(str(LEDGER_DB_PATH)) as c:
            c.execute("UPDATE filesystem_entry SET status=?, scan_date=? WHERE path=?", 
                     (status, time.time(), file_path_str))
        processed_count += 1
        
    print(f"✅ Passive Zone Scan Complete. Processed {processed_count} files.")

if __name__ == "__main__":
    main()
