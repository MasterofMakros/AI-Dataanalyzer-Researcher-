"""
Batch Processor Pilot (The Golden Hour)
Phase 4: Processing the 5,000 "Golden Dataset" files.
Features:
- Native PyMuPDF Extraction (Fast)
- Author Extraction (PDF Metadata)
- Smart Status Updates
"""

import sqlite3
import time
import sys
import fitz  # PyMuPDF
from pathlib import Path

# Import tools
sys.path.insert(0, str(Path(__file__).parent))
from smart_ingest import (
    sha256_hash, 
    get_mime_type, 
    save_to_shadow_ledger
)

# Configuration
from config.paths import LEDGER_DB_PATH
MAIN_LEDGER = str(LEDGER_DB_PATH).replace("shadow_ledger.db", "ledger.db") # Assuming default ledger name is ledger.db in the same dir?
# Or if ledger.db is separate. Let's look at paths.py, it says LEDGER_DB_PATH is shadow_ledger.db. 
# Original code had MAIN_LEDGER at "F:/conductor/ledger.db" and SHADOW at "F:/conductor/data/shadow_ledger.db"
# Wait, paths.py defines LEDGER_DB_PATH as "data/shadow_ledger.db".
# So MAIN_LEDGER (the real one?) was at root "conductor/ledger.db".
# I should probably defined MAIN_LEDGER_PATH in paths.py or just construct it relative to BASE_DIR.

MAIN_LEDGER = str(LEDGER_DB_PATH.parent.parent / "ledger.db") # ../../ledger.db
SHADOW_LEDGER = str(LEDGER_DB_PATH)

# --- OFFLINE MODE OVERRIDES ---
def mock_get_mime_type(filepath: Path) -> str:
    return "application/pdf"

def mock_classify(text, filename):
    return {
        "category": "Pilot_Phase4",
        "subcategory": "Golden_Dataset",
        "confidence": 1.0,
        "tags": ["pilot", "phase4"],
        "meta_description": f"Pilot Doc: {filename}"
    }
# -----------------------------

def ensure_columns():
    """Ensures Shadow Ledger has extra columns for Graph Data."""
    conn = sqlite3.connect(SHADOW_LEDGER)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE files ADD COLUMN author TEXT")
        cursor.execute("ALTER TABLE files ADD COLUMN keywords TEXT") # JSON list
        print("🔧 Added 'author' and 'keywords' columns.")
    except sqlite3.OperationalError:
        pass # Already exist
    conn.commit()
    conn.close()

def fetch_pilot_candidates():
    """Fetches valid paths from Main Ledger where pilot_flag=1."""
    conn = sqlite3.connect(MAIN_LEDGER)
    cursor = conn.cursor()
    
    query = """
        SELECT path FROM filesystem_entry 
        WHERE pilot_flag = 1 
        AND (ingest_status IS NULL OR ingest_status != 'DONE')
    """
    cursor.execute(query)
    files = [row[0] for row in cursor.fetchall()]
    conn.close()
    return files

def update_status(path: str, status: str):
    conn = sqlite3.connect(MAIN_LEDGER)
    conn.execute("UPDATE filesystem_entry SET ingest_status = ? WHERE path = ?", (status, path))
    conn.commit()
    conn.close()

def process_pdf(filepath: Path):
    """Processes a single PDF for the Pilot."""
    try:
        # 1. Metadaten
        file_hash = sha256_hash(filepath)
        stats = filepath.stat()
        
        data = {
            "sha256": file_hash,
            "original_filename": filepath.name,
            "current_filename": filepath.name,
            "original_path": str(filepath),
            "current_path": str(filepath),
            "file_size": stats.st_size,
            "mime_type": "application/pdf",
            "status": "indexed_pilot"
        }
        
        # 2. PyMuPDF Extraction
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        
        data["extracted_text"] = text.strip()
        
        # 3. Metadata (Author)
        meta = doc.metadata
        if meta:
            data["author"] = meta.get("author", "")
            data["keywords"] = meta.get("keywords", "") # From PDF properties
        
        # 4. Mock Classify
        data.update(mock_classify(text, filepath.name))
        
        # 5. Save
        save_to_shadow_ledger(data)
        
        # Update extra columns manually (save_to_shadow_ledger might not handle them)
        conn = sqlite3.connect(SHADOW_LEDGER)
        conn.execute("UPDATE files SET author=?, keywords=? WHERE sha256=?", 
                    (data.get("author"), data.get("keywords"), file_hash))
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error {filepath.name}: {e}")
        return False

def run_pilot():
    ensure_columns()
    files = fetch_pilot_candidates()
    print(f"🚀 Starting Phase 4 Pilot: {len(files)} Docs")
    
    success = 0
    start = time.time()
    
    for i, f in enumerate(files):
        path = Path(f)
        if not path.exists():
            update_status(f, "MISSING")
            continue
            
        print(f"[{i+1}/{len(files)}] {path.name[:40]}...")
        if process_pdf(path):
            update_status(f, "DONE")
            success += 1
        else:
            update_status(f, "FAILED")
            
    duration = time.time() - start
    print(f"✅ Pilot Batch Complete. {success}/{len(files)} in {duration:.2f}s")

if __name__ == "__main__":
    run_pilot()
