"""
Vector Service (Native)
Phase 3: High-Performance Embedding Generation (Docker-Free)
Uses sentence-transformers (all-MiniLM-L6-v2) for fast CPU inference.
"""

from sentence_transformers import SentenceTransformer
import sqlite3
import json
import time
from typing import List, Dict, Any
import numpy as np

# Konfiguration
from config.paths import LEDGER_DB_PATH

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2" # Besser für Deutsch/Multilingual
LEDGER_DB = LEDGER_DB_PATH

class VectorService:
    def __init__(self):
        print(f"🚀 Loading Embedding Model: {MODEL_NAME}...")
        self.model = SentenceTransformer(MODEL_NAME)
        self.embedding_dimension = 384
        print("✅ Model loaded.")

    def embed_text(self, text: str, filename: str = "") -> List[float]:
        """Generiert Embedding mit Smart-Context Strategie."""
        if not text:
            return [0.0] * self.embedding_dimension
        
        # Smart Context: Filename + Start (500) + Middle (500)
        # Dies fängt den Titel UND den Kerninhalt
        text_len = len(text)
        start_chunk = text[:800]
        
        middle_start = text_len // 2
        middle_chunk = text[middle_start:middle_start+800] if text_len > 1600 else ""
        
        combined_text = f"Filename: {filename}\nContent: {start_chunk} ... {middle_chunk}"
        
        return self.model.encode(combined_text[:2000]).tolist()

    def process_queue(self, batch_size=50):
        """Verarbeitet Dateien aus dem Ledger, die noch keine Embeddings haben."""
        conn = sqlite3.connect(LEDGER_DB)
        cursor = conn.cursor()
        
        # Check column
        try:
            cursor.execute("SELECT embedding_status FROM files LIMIT 1")
        except sqlite3.OperationalError:
            print("🔧 Adding embedding columns to schema...")
            cursor.execute("ALTER TABLE files ADD COLUMN embedding_status TEXT DEFAULT 'PENDING'")
            cursor.execute("ALTER TABLE files ADD COLUMN embedding_blob BLOB")
            conn.commit()

        # Fetch pending
        query = """
            SELECT id, extracted_text, original_filename FROM files 
            WHERE (status='indexed_passive' OR status='indexed_pilot') 
            AND (embedding_status IS NULL OR embedding_status='PENDING')
            AND length(extracted_text) > 50
            LIMIT ?
        """
        cursor.execute(query, (batch_size,))
        rows = cursor.fetchall()
        
        if not rows:
            print("📭 No pending contents for vectorization.")
            conn.close()
            return 0

        print(f"🧬 Vectorizing {len(rows)} documents (Multilingual)...")
        updates = []
        
        start = time.time()
        for doc_id, text, filename in rows:
            try:
                vec = self.embed_text(text, filename)
                # Store as binary blob (float32 bytes) for efficiency
                vec_blob = np.array(vec, dtype=np.float32).tobytes()
                updates.append((vec_blob, "DONE", doc_id))
            except Exception as e:
                print(f"❌ Error doc {doc_id}: {e}")
                updates.append((None, "FAILED", doc_id))

        # Bulk Update
        cursor.executemany("UPDATE files SET embedding_blob=?, embedding_status=? WHERE id=?", updates)
        conn.commit()
        conn.close()
        
        duration = time.time() - start
        rate = len(rows) / duration
        print(f"✅ Vectorized {len(rows)} docs in {duration:.2f}s ({rate:.1f} docs/s)")
        return len(rows)

if __name__ == "__main__":
    service = VectorService()
    print("⏳ Vector Service Daemon started...")
    
    no_work_strikes = 0
    
    while True:
        try:
            count = service.process_queue(batch_size=50)
            if count == 0:
                no_work_strikes += 1
                if no_work_strikes > 10:
                    print("💤 Idle... (Waiting for input)")
                    time.sleep(10)
                else:
                    time.sleep(2)
            else:
                no_work_strikes = 0
        except KeyboardInterrupt:
            print("🛑 Stopping Service.")
            break
        except Exception as e:
            print(f"❌ Critical Error: {e}")
            time.sleep(5)
