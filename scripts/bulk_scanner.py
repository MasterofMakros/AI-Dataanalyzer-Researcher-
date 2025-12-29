"""
Bulk Scanner Engine (The Scout)
Phase 3 Activation: High-Speed Filesystem Inventory
"""

import os
import sqlite3
import time
from pathlib import Path
from typing import List, Tuple, Set

# Configuration
from config.paths import BASE_DIR, LEDGER_DB_PATH

ROOT_DIR = str(BASE_DIR).split(os.sep)[0] + os.sep if os.name == 'nt' else "/"  # Start scan root (Drive root on Windows or / on Linux)
# Or better, let's just make it configurable or default to "F:/" only on Windows if Env not set. 
# But for now, let's assume we scan the drive where BASE_DIR is located or just "."
# The original code scanned "F:/". Let's stick to scanning the drive of BASE_DIR for now or just generic.
# Actually, let's use the drive of BASE_DIR
ROOT_DIR = os.path.splitdrive(BASE_DIR)[0] + "/" if os.name == 'nt' else "/"

DB_PATH = str(LEDGER_DB_PATH)
BATCH_SIZE = 10000

# Triage configuration
INTERESTING_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", 
    ".txt", ".md", ".markdown", ".csv", ".json", ".xml", ".yml", ".yaml", 
    ".py", ".js", ".ts", ".rs", ".go", ".c", ".cpp", ".h", ".java",
    ".eml", ".msg", ".html", ".htm",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg" # For multimodal
}

IGNORED_DIRS = {
    "$RECYCLE.BIN", "System Volume Information", ".git", ".gemini", 
    "node_modules", "__pycache__", "Windows", "Program Files", "Program Files (x86)"
}

class BulkScanner:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialisiert die SQLite-Datenbank (Shadow Ledger)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Performance Tuning for SQLite
        cursor.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging
        cursor.execute("PRAGMA synchronous = NORMAL;") 
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS filesystem_entry (
                path TEXT PRIMARY KEY,
                filename TEXT,
                extension TEXT,
                size_bytes INTEGER,
                modified_timestamp REAL,
                status TEXT DEFAULT 'DISCOVERED',
                scan_date REAL
            )
        """)
        
        # Index for fast triage queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON filesystem_entry(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ext ON filesystem_entry(extension);")
        
        conn.commit()
        conn.close()

    def determine_status(self, ext: str) -> str:
        """Simple Triage Logic."""
        if ext.lower() in INTERESTING_EXTENSIONS:
            return "READY_FOR_INGEST"
        return "IGNORED"

    def scan(self, start_path: str):
        """Führt den Bulk-Scan durch."""
        print(f"Starting Bulk Scan on: {start_path}")
        print(f"Ledger: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_time = time.time()
        count = 0
        batch_data = []
        
        for root, dirs, files in os.walk(start_path):
            # In-place filtering of directories to prevent recursion into ignored paths
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            
            for name in files:
                try:
                    path = os.path.join(root, name)
                    stats = os.stat(path)
                    
                    ext = os.path.splitext(name)[1].lower()
                    status = self.determine_status(ext)
                    
                    batch_data.append((
                        path, 
                        name, 
                        ext, 
                        stats.st_size, 
                        stats.st_mtime, 
                        status, 
                        time.time()
                    ))
                    
                    count += 1
                    
                    if len(batch_data) >= BATCH_SIZE:
                        self._commit_batch(cursor, batch_data)
                        duration = time.time() - start_time
                        rate = count / duration if duration > 0 else 0
                        print(f"Scanned {count} files... (Rate: {rate:.0f} files/s)")
                        batch_data = [] # Reset
                        
                except OSError as e:
                    # Permission denied, etc.
                    continue
        
        # Final commit
        if batch_data:
            self._commit_batch(cursor, batch_data)
            
        conn.commit()
        conn.close()
        
        total_time = time.time() - start_time
        print(f"\n--- Scan Complete ---")
        print(f"Total Files: {count}")
        print(f"Time: {total_time:.2f}s")
        print(f"Avg Rate: {count / total_time:.0f} files/s")

    def _commit_batch(self, cursor, data: List[Tuple]):
        """Bulk Insert / Replace."""
        cursor.executemany("""
            INSERT OR REPLACE INTO filesystem_entry 
            (path, filename, extension, size_bytes, modified_timestamp, status, scan_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data)
        cursor.connection.commit()

if __name__ == "__main__":
    # Ensure directory exists
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    scanner = BulkScanner(DB_PATH)
    
    # Run Validation Scan first (e.g., on Conductor folder)
    # scanner.scan(str(BASE_DIR))
    
    # Or Full Scan (commented out for safety in script, enable via CLI argument ideally)
    # For this execution, we default to ROOT_DIR but maybe restricted
    print(f"WARNING: Starting Full Scan on {ROOT_DIR} in 5 seconds... CTRL+C to cancel.")
    time.sleep(5)
    scanner.scan(ROOT_DIR)
