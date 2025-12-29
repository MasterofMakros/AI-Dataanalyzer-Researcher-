
import sqlite3
import os

from config.paths import LEDGER_DB_PATH

DB_PATH = LEDGER_DB_PATH

def check_status():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total Files
    cursor.execute("SELECT COUNT(*) FROM files")
    total = cursor.fetchone()[0]
    
    # Processed Text
    cursor.execute("SELECT COUNT(*) FROM files WHERE extracted_text IS NOT NULL AND length(extracted_text) > 0")
    extracted = cursor.fetchone()[0]
    
    # Vectorized (Assuming embedding_status or non-null blob if column exists)
    # Checking schema first
    cursor.execute("PRAGMA table_info(files)")
    cols = [r[1] for r in cursor.fetchall()]
    
    vectorized = 0
    if "embedding_blob" in cols:
        cursor.execute("SELECT COUNT(*) FROM files WHERE embedding_blob IS NOT NULL")
        vectorized = cursor.fetchone()[0]
    elif "embedding_status" in cols:
         cursor.execute("SELECT COUNT(*) FROM files WHERE embedding_status='DONE'")
         vectorized = cursor.fetchone()[0]
         
    # Pilot Flag check
    pilot_count = 0
    if "pilot_flag" in cols:
        cursor.execute("SELECT COUNT(*) FROM files WHERE pilot_flag=1")
        pilot_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM files WHERE pilot_flag=1 AND extracted_text IS NOT NULL AND length(extracted_text) > 0")
        pilot_extracted = cursor.fetchone()[0]
        
        print("\n📊 AMPLIFY PILOT STATUS (Phase 4)")
        print("="*40)
        print(f"Target Set:     {pilot_count} / 5000")
        print(f"Extracted:      {pilot_extracted} ({pilot_extracted/pilot_count:.1%})")
        # print(f"Vectorized:     {pilot_vectorized} ...") # Logic complex depending on schema
    else:
        print("\n⚠️ 'pilot_flag' column missing - showing global stats.")

    print("\n🌍 GLOBAL LEDGER STATS")
    print("="*40)
    print(f"Total Files:    {total}")
    print(f"Extracted:      {extracted}")
    print(f"Vectorized:     {vectorized}")
    
    conn.close()

if __name__ == "__main__":
    check_status()
