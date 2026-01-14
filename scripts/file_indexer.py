"""
Neural Vault File Indexer - MVP Version
Indexiert Dateien in Qdrant

Usage:
    python file_indexer.py --path /path/to/folder --limit 100
"""

import os
import sys
import json
import hashlib
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
# Add project root to path
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.paths import BASE_DIR

# Konfiguration aus .env
TIKA_URL = "http://localhost:9998/tika"
QDRANT_URL = "http://localhost:6335"
OLLAMA_URL = "http://localhost:11435"

# Keys aus .env laden
def load_env():
    env_path = BASE_DIR / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
    return env

ENV = load_env()
QDRANT_KEY = ENV.get("QDRANT_API_KEY", "")

# Unterstützte Dateitypen für Volltext
TEXT_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md", ".rtf",
    ".xlsx", ".xls", ".csv", ".json", ".xml",
    ".html", ".htm", ".eml", ".msg"
}

def sha256_hash(filepath: Path) -> str:
    """Berechne SHA-256 Hash einer Datei."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def extract_text_tika(filepath: Path) -> Optional[str]:
    """Extrahiere Text via Apache Tika."""
    try:
        with open(filepath, "rb") as f:
            response = requests.put(
                TIKA_URL,
                data=f,
                headers={"Accept": "text/plain"},
                timeout=60
            )
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"  WARN Tika Fehler: {e}")
    return None

def generate_embedding(text: str) -> Optional[List[float]]:
    """Generiere Embedding via Ollama."""
    try:
        # Truncate text to avoid OOM
        text = text[:8000]
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={
                "model": "nomic-embed-text",
                "prompt": text
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("embedding")
    except Exception as e:
        print(f"  WARN Embedding Fehler: {e}")
    return None

def classify_with_ollama(text: str, filename: str) -> Dict[str, Any]:
    """Klassifiziere Dokument via Ollama."""
    prompt = f"""Analysiere diese Datei und antworte NUR mit JSON.

Dateiname: {filename}
Text (Auszug): {text[:2000]}

Antworte mit exakt diesem JSON-Format:
{{
    "category": "Finanzen|Arbeit|Privat|Medien|Dokumente|Sonstiges",
    "subcategory": "z.B. Rechnung, Vertrag, Foto",
    "confidence": 0.0-1.0,
    "meta_description": "1-2 Sätze: Worum geht es?",
    "tags": ["tag1", "tag2"]
}}"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=120
        )
        if response.status_code == 200:
            result = response.json().get("response", "{}")
            return json.loads(result)
    except Exception as e:
        print(f"  WARN Classification Fehler: {e}")
    
    return {
        "category": "Sonstiges",
        "subcategory": "Unbekannt",
        "confidence": 0.0,
        "meta_description": f"Datei: {filename}",
        "tags": []
    }

def index_to_qdrant(doc_id: str, vector: List[float], payload: Dict):
    """Indexiere Vektor in Qdrant."""
    headers = {"api-key": QDRANT_KEY}
    response = requests.put(
        f"{QDRANT_URL}/collections/neural_vault/points",
        headers=headers,
        json={
            "points": [{
                "id": hash(doc_id) % (2**63),
                "vector": vector,
                "payload": payload
            }]
        },
        timeout=30
    )
    return response.status_code == 200

def process_file(filepath: Path) -> Optional[Dict]:
    """Verarbeite eine einzelne Datei."""
    stats = filepath.stat()
    file_hash = sha256_hash(filepath)
    
    doc = {
        "id": file_hash,
        "original_filename": filepath.name,
        "current_path": str(filepath),
        "file_size": stats.st_size,
        "file_created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "file_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "extension": filepath.suffix.lower(),
        "indexed_at": datetime.now().isoformat()
    }
    
    # Text extrahieren für unterstützte Formate
    if filepath.suffix.lower() in TEXT_EXTENSIONS:
        print("  INFO Extrahiere Text...")
        text = extract_text_tika(filepath)
        if text:
            doc["extracted_text"] = text[:50000]  # Limit
            
            # Klassifizieren
            print("  INFO Klassifiziere...")
            classification = classify_with_ollama(text, filepath.name)
            doc.update(classification)
    else:
        doc["extracted_text"] = ""
        doc["category"] = "Medien" if filepath.suffix.lower() in {".jpg", ".png", ".mp4"} else "Sonstiges"
        doc["meta_description"] = f"Datei: {filepath.name}"
        doc["tags"] = []
    
    return doc

def main(path: str, limit: int = 100):
    """Hauptfunktion: Indexiere Dateien."""
    root = Path(path)
    if not root.exists():
        print(f"FAIL Pfad existiert nicht: {path}")
        sys.exit(1)
    
    print(f"START Indexierung: {path}")
    print(f"   Limit: {limit} Dateien")
    print("-" * 50)
    
    files = [f for f in root.rglob("*") if f.is_file()][:limit]
    total = len(files)
    success = 0
    errors = 0
    start_time = time.time()
    
    for i, filepath in enumerate(files, 1):
        print(f"\n[{i}/{total}] {filepath.name}")
        
        try:
            doc = process_file(filepath)
            if not doc:
                errors += 1
                continue
            
            text_for_embedding = doc.get("extracted_text") or doc.get("meta_description", "")
            vector = generate_embedding(text_for_embedding)
            if not vector:
                print("  FAIL Kein Embedding erzeugt")
                errors += 1
                continue

            payload = doc.copy()
            payload["file_path"] = payload.pop("current_path", "")

            print("  INFO Indexiere in Qdrant...")
            if index_to_qdrant(doc["id"], vector, payload):
                success += 1
            else:
                errors += 1
                
        except Exception as e:
            print(f"  FAIL Fehler: {e}")
            errors += 1
    
    duration = time.time() - start_time
    rate = success / duration if duration > 0 else 0
    
    print("\n" + "=" * 50)
    print("DONE")
    print(f"   Erfolgreich: {success}/{total}")
    print(f"   Fehler: {errors}")
    print(f"   Dauer: {duration:.1f}s")
    print(f"   Rate: {rate:.1f} Docs/Sekunde")

if __name__ == "__main__":
    def parse_args():
        import argparse
        parser = argparse.ArgumentParser(description="Indiziere Dateien für Neural Vault")
        # Default to a test folder in BASE_DIR if not specified, or leave as required
        default_path = str(BASE_DIR / "_TestFolder") 
        parser.add_argument("--path", default=default_path, help="Pfad zum Indexieren")
        parser.add_argument("--limit", type=int, default=100, help="Max. Anzahl Dateien")
        return parser.parse_args()

    args = parse_args()
    main(args.path, args.limit)
