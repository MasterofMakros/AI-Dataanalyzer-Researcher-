"""
Batch Processor (The Deep Diver)
Phase 3: Processing existing assets from the Inventory (Passive Zone).
DOES NOT MOVE FILES - ONLY INDEXES.
"""

import sqlite3
import time
import sys
import fitz  # PyMuPDF
from pathlib import Path

# Import tools from smart_ingest
sys.path.insert(0, str(Path(__file__).parent))
from smart_ingest import (
    extract_text_tika, 
    classify_with_ollama, 
    sha256_hash, 
    get_mime_type, 
    save_to_shadow_ledger,
    EXTENDED_AVAILABLE,
    EXTENDED_EXTENSIONS,
    TEXT_EXTENSIONS
)

if EXTENDED_AVAILABLE:
    from extended_file_processor import process_extended_file

import smart_ingest
from config.paths import BASE_DIR

# --- OFFLINE MODE OVERRIDES (Docker Down) ---
print("⚠️ OFFLINE MODE: Disabling Tika/Ollama calls to avoid timeouts.")

def mock_get_mime_type(filepath: Path) -> str:
    ext = filepath.suffix.lower()
    mimes = {
        ".pdf": "application/pdf", 
        ".txt": "text/plain", 
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".eml": "message/rfc822"
    }
    return mimes.get(ext, "application/octet-stream")

def mock_classify(text, filename, mime=""):
    # Simple Heuristic Classification
    cat = "Dokumente"
    if ".pdf" in filename.lower(): cat = "Dokumente"
    
    return {
        "category": cat,
        "subcategory": "Batch_Import",
        "confidence": 0.5,
        "tags": ["offline_batch"],
        "meta_description": f"Offline Import: {filename}",
        "_anti_hallucination": False
    }

# Patch output
smart_ingest.get_mime_type = mock_get_mime_type
smart_ingest.classify_with_ollama = mock_classify

# CRITICAL: Update local references imported from smart_ingest
get_mime_type = mock_get_mime_type
classify_with_ollama = mock_classify
# ---------------------------------------------

from config.paths import BASE_DIR

# Main Ledger (Inventory)
LEDGER_DB = BASE_DIR / "ledger.db"

def fetch_candidates(limit: int = 1000, extension: str = ".pdf"):
    """Holt 'READY_FOR_INGEST' Dateien aus dem Ledger."""
    conn = sqlite3.connect(LEDGER_DB)
    cursor = conn.cursor()
    
    # Pruefen ob spalte 'ingest_status' existiert, sonst anlegen
    try:
        cursor.execute("SELECT ingest_status FROM filesystem_entry LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE filesystem_entry ADD COLUMN ingest_status TEXT DEFAULT 'PENDING'")
        conn.commit()
    
    query = """
        SELECT path FROM filesystem_entry 
        WHERE extension = ? 
        AND status = 'READY_FOR_INGEST' 
        AND (ingest_status IS NULL OR ingest_status = 'PENDING')
        LIMIT ?
    """
    
    cursor.execute(query, (extension, limit))
    files = [row[0] for row in cursor.fetchall()]
    conn.close()
    return files

def update_ledger_status(path: str, status: str):
    conn = sqlite3.connect(LEDGER_DB)
    cursor = conn.cursor()
    cursor.execute("UPDATE filesystem_entry SET ingest_status = ? WHERE path = ?", (status, path))
    conn.commit()
    conn.close()

def extract_pdf_native(filepath: Path) -> str:
    """Extrahiert Text aus PDF mit PyMuPDF (Native Speed)."""
    try:
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"  ❌ PDF Native Error: {e}")
        return ""

def process_passive_file(filepath: Path):
    """
    Verarbeitet eine Datei OHNE sie zu verschieben (Passive Mode).
    """
    print(f"\n📄 Processing: {filepath.name}")
    try:
        # 1. Metadaten
        file_hash = sha256_hash(filepath)
        mime_type = get_mime_type(filepath) # Trough Tika if avail, but we know Tika is down... 
        # Actually get_mime_type uses Tika. If Tika is down, it returns application/octet-stream.
        # We can trust extension for now or use python-magic if needed, but extension is fine for 99%.
        
        stats = filepath.stat()
        
        data = {
            "sha256": file_hash,
            "original_filename": filepath.name,
            "current_filename": filepath.name, # Keine Umbenennung
            "original_path": str(filepath),
            "current_path": str(filepath),     # Pfad bleibt gleich
            "file_size": stats.st_size,
            "mime_type": mime_type,
            "status": "indexed_passive"
        }
        
        # 2. Text Extraktion
        ext = filepath.suffix.lower()
        print(f"  🔍 Extracting text ({ext})...")
        
        if ext == ".pdf":
            # Prefer Native PyMuPDF over Tika (Challenger Winner Strategy)
            text = extract_pdf_native(filepath)
            if not text:
                print("  ⚠️ Native PDF extraction empty, trying Tika fallback...")
                text = extract_text_tika(filepath) or ""
            data["extracted_text"] = text
            data["extraction_source"] = "pymupdf_native"
            
        elif EXTENDED_AVAILABLE and ext in EXTENDED_EXTENSIONS:
            ext_result = process_extended_file(filepath)
            data["extracted_text"] = ext_result.extracted_text if ext_result.success else ""
            data["extraction_source"] = "extended_processor"
            
        elif ext in TEXT_EXTENSIONS:
            # Native fallback for txt/md?
            if ext in [".txt", ".md", ".json", ".xml", ".csv", ".py", ".js", ".html", ".htm"]:
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        data["extracted_text"] = f.read()
                    data["extraction_source"] = "native_text"
                except:
                    data["extracted_text"] = extract_text_tika(filepath) or ""
            else:
                data["extracted_text"] = extract_text_tika(filepath) or ""
        else:
            data["extracted_text"] = ""
            
        # 3. Klassifizierung (fuer Metadaten)
        print("  🧠 Classifying...")
        # Note: classify_with_ollama uses Ollama (Port 11435). This should work if Ollama is up.
        # Ollama container 8e43d625ae39 was UP in step 8408.
        # Assuming only Docker Desktop API is flaky but containers might be still running?
        # Or if Docker is down-down, Ollama is also down.
        # If Ollama is down, classify_with_ollama returns default.
        
        classification = classify_with_ollama(
            data.get("extracted_text", "")[:5000], # Max query length
            filepath.name
        )
        data.update(classification)
        
        # 4. Speichern (Shadow Ledger only in Offline Mode)
        print("  💾 Indexing (Ledger)...")
        save_to_shadow_ledger(data)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def run_batch(limit=1000, file_type=".pdf"):
    print(f"🚀 Starting Batch Processor: {limit} x {file_type} (Native Mode)")
    
    candidates = fetch_candidates(limit, file_type)
    print(f"📋 Found {len(candidates)} candidates.")
    
    success = 0
    start_time = time.time()
    
    for i, path_str in enumerate(candidates):
        path = Path(path_str)
        if not path.exists():
            print(f"⚠️ File missing: {path}")
            update_ledger_status(path_str, "MISSING")
            continue
            
        print(f"[{i+1}/{len(candidates)}] Processing...")
        if process_passive_file(path):
            update_ledger_status(path_str, "DONE")
            success += 1
        else:
            update_ledger_status(path_str, "FAILED")
            
    duration = time.time() - start_time
    print(f"\n✅ Batch Complete.")
    print(f"Success: {success}/{len(candidates)}")
    print(f"Time: {duration:.2f}s")
    if len(candidates) > 0:
        print(f"Avg Speed: {duration/len(candidates):.2f}s/doc")

if __name__ == "__main__":
    # Default 1000 PDFs
    run_batch(1000, ".pdf")
