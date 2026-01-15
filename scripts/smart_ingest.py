"""
Neural Vault Smart Ingestion - Phase 2
Automatische Verarbeitung von Dateien in _Inbox

Usage:
    python smart_ingest.py --watch       # Kontinuierlich überwachen
    python smart_ingest.py --once        # Einmal durchlaufen
"""

import os
import sys
import json
import shutil
import hashlib
import requests
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Ensure repo root is on sys.path for config imports when launched from elsewhere.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Importiere Quality Gates
sys.path.insert(0, str(Path(__file__).parent))
from quality_gates import (
    run_quality_gates, 
    generate_smart_filename, 
    determine_target_folder,
    GateResult, QualityResult
)

# Importiere Extended File Processors für neue Dateitypen
try:
    from extended_file_processor import (
        is_extended_processable,
        process_extended_file,
        get_supported_extensions
    )
    EXTENDED_EXTENSIONS = set(get_supported_extensions())
    EXTENDED_AVAILABLE = True
except ImportError:
    EXTENDED_EXTENSIONS = set()
    EXTENDED_AVAILABLE = False
    print("[WARN] extended_file_processor nicht verfügbar")

# Enhanced Extraction (Magic Bytes, HTML→Markdown, Context Headers)
try:
    from scripts.utils.enhanced_extraction import (
        detect_file_type,
        extract_text_enhanced,
        get_all_supported_extensions as get_enhanced_extensions,
        FileTypeInfo
    )
    ENHANCED_EXTRACTION_AVAILABLE = True
    ENHANCED_EXTENSIONS = get_enhanced_extensions()
    print(f"[INFO] Enhanced Extraction verfügbar: {len(ENHANCED_EXTENSIONS)} Formate")
except ImportError as e:
    ENHANCED_EXTRACTION_AVAILABLE = False
    ENHANCED_EXTENSIONS = set()
    print(f"[WARN] Enhanced Extraction nicht verfügbar: {e}")

# Data Narrator Integration (ABT-N02)
try:
    import pandas as pd
    from scripts.experimental.data_narrator import narrate_table
    from config.feature_flags import is_enabled
    DATA_NARRATOR_AVAILABLE = True
except ImportError as e:
    DATA_NARRATOR_AVAILABLE = False
    print(f"[WARN] Data Narrator nicht verfügbar: {e}")

# Deep Structure Integration (ABT-B04)
try:
    from scripts.deep_ingest import DeepIngestService
    DOCLING_AVAILABLE = True
    print("[INFO] Docling (Deep Structure) verfügbar")
except ImportError as e:
    DOCLING_AVAILABLE = False
    print(f"[WARN] Docling nicht verfügbar: {e}")

# Unified Extraction Service (Docling-First Routing)
try:
    from scripts.services.extraction_service import (
        extract_text as unified_extract,
        get_extraction_stats,
        ExtractionResult
    )
    from config.parser_routing import get_parser, ParserType
    UNIFIED_EXTRACTION_AVAILABLE = True
    stats = get_extraction_stats()
    available_count = sum(1 for v in stats["services"].values() if v)
    print(f"[INFO] Unified Extraction Service: {available_count}/4 Services verfügbar")
except ImportError as e:
    UNIFIED_EXTRACTION_AVAILABLE = False
    print(f"[WARN] Unified Extraction nicht verfügbar: {e}")

# Docker Parser Service Client (bevorzugt für Produktion)
try:
    from parser_service_client import (
        parse_file_docker,
        is_parser_available,
        is_docker_processable,
        get_supported_extensions as get_docker_extensions
    )
    DOCKER_PARSER_AVAILABLE = is_parser_available()
    if DOCKER_PARSER_AVAILABLE:
        DOCKER_EXTENSIONS = set(get_docker_extensions())
        print(f"[INFO] Docker Parser Service verfügbar: {len(DOCKER_EXTENSIONS)} Formate")
    else:
        DOCKER_EXTENSIONS = set()
except ImportError:
    DOCKER_PARSER_AVAILABLE = False
    DOCKER_EXTENSIONS = set()
    print("[WARN] parser_service_client nicht verfügbar")

# Konfiguration
# Konfiguration
from config.paths import (
    INBOX_DIR, QUARANTINE_DIR, LEDGER_DB_PATH, BASE_DIR,
    TIKA_URL, QDRANT_URL, OLLAMA_URL
)

INBOX_PATH = INBOX_DIR
QUARANTINE_BASE = QUARANTINE_DIR
SHADOW_LEDGER_PATH = LEDGER_DB_PATH

# Keys aus .env laden
def load_env():
    env_path = BASE_DIR / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
    return env

ENV = load_env()
QDRANT_KEY = os.environ.get("QDRANT_API_KEY") or ENV.get("QDRANT_API_KEY", "")
TELEGRAM_TOKEN = ENV.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = ENV.get("TELEGRAM_CHAT_ID", "")

# Unterstützte Dateitypen
TEXT_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md", ".rtf",
    ".xlsx", ".xls", ".csv", ".json", ".xml",
    ".html", ".htm"
}

# Merge mit Extended/Enhanced Extensions für vollständige Unterstützung
ALL_SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | EXTENDED_EXTENSIONS | DOCKER_EXTENSIONS | ENHANCED_EXTENSIONS

def init_shadow_ledger():
    """Initialisiert die Shadow Ledger Datenbank."""
    SHADOW_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(SHADOW_LEDGER_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sha256 TEXT UNIQUE NOT NULL,
            original_filename TEXT NOT NULL,
            current_filename TEXT NOT NULL,
            original_path TEXT NOT NULL,
            current_path TEXT NOT NULL,
            file_size INTEGER,
            mime_type TEXT,
            category TEXT,
            subcategory TEXT,
            confidence REAL,
            extracted_text TEXT,
            meta_description TEXT,
            tags TEXT,
            status TEXT DEFAULT 'indexed',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("📊 Shadow Ledger initialisiert")

def sha256_hash(filepath: Path) -> str:
    """Berechne SHA-256 Hash einer Datei."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def get_mime_type(filepath: Path) -> str:
    """Ermittle MIME-Type via Magic Bytes oder Tika."""
    # Bevorzugt: Magic Byte Detection
    if ENHANCED_EXTRACTION_AVAILABLE:
        try:
            file_info = detect_file_type(filepath)
            if file_info.mime_type != "application/octet-stream":
                return file_info.mime_type
        except Exception as e:
            print(f"  ⚠️ Magic Detection Fehler: {e}")

    # Fallback: Tika
    try:
        with open(filepath, "rb") as f:
            response = requests.put(
                "http://localhost:9998/detect/stream",
                data=f,
                headers={"Accept": "text/plain"},
                timeout=30
            )
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"  ⚠️ MIME-Type Fehler: {e}")
    return "application/octet-stream"

def extract_text_tika(filepath: Path, prefer_markdown: bool = True) -> Optional[str]:
    """
    Extrahiere Text via Apache Tika.

    Args:
        filepath: Pfad zur Datei
        prefer_markdown: HTML holen und zu Markdown konvertieren (Tabellenerhalt)

    Returns:
        Extrahierter Text oder None
    """
    # Bevorzugt: Enhanced Extraction mit HTML→Markdown
    if ENHANCED_EXTRACTION_AVAILABLE and prefer_markdown:
        try:
            text, fmt = extract_text_enhanced(filepath, prefer_markdown=True)
            if text:
                print(f"     ✅ Enhanced Extraction: {fmt}")
                return text
        except Exception as e:
            print(f"  ⚠️ Enhanced Extraction Fehler: {e}")

    # Fallback: Standard Tika Plain Text
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
        print(f"  ⚠️ Tika Fehler: {e}")
    return None

# PII Masking (ABT-B06)
def mask_sensitive_data(text: str) -> str:
    """Maskiert PII (Namen, IBANs) via Neural Worker."""
    if not is_enabled("USE_PII_MASKING"):
        return text

    # Skip if text is too short or empty
    if not text or len(text) < 10:
        return text

    try:
        # Call Neural Worker
        NEURAL_WORKER_URL = "http://localhost:8005" 
        response = requests.post(
            f"{NEURAL_WORKER_URL}/process/pii", 
            json={
                "text": text[:100000],  # Limit payload
                "labels": ["person", "iban", "phone_number", "email"]
            }, 
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"     ⚠️ PII Masking API Fehler: {response.status_code}")
            return text
            
        entities = response.json().get("entities", [])
        if not entities:
            return text
            
        # Replace entities (reverse order to keep indices valid)
        # Sort by start index descending
        entities.sort(key=lambda x: x["start"], reverse=True)
        
        masked_text = text
        masked_count = 0
        
        for ent in entities:
            if ent["score"] > 0.6: # Confidence threshold
                start = ent["start"]
                end = ent["end"]
                label = ent["label"].upper()
                curr_text = list(masked_text)
                # Replace with [LABEL]
                mask = f"[{label}]"
                masked_text = masked_text[:start] + mask + masked_text[end:]
                masked_count += 1
                
        if masked_count > 0:
            print(f"     🛡️ PII Masking: {masked_count} Entitäten maskiert")
            
        return masked_text

    except Exception as e:
        print(f"     ⚠️ PII Masking Exception: {e}")
        return text

# Classification Router Integration
try:
    # Add project root to path
    sys.path.append(str(Path(__file__).parent.parent))
    from services.classifier import ClassificationRouter
    CLASSIFIER = ClassificationRouter()
    print("✅ Classification Router geladen")
except ImportError as e:
    print(f"⚠️ Classification Router Fehler: {e}")
    CLASSIFIER = None

def classify_with_ollama(text: str, filename: str, mime_type: str = "unknown") -> Dict[str, Any]:
    """
    DEPRECATED WRAPPER: Delegiert an ClassificationRouter.
    Der Name bleibt vorerst gleich, um Kompatibilität zu wahren.
    """
    if CLASSIFIER:
        return CLASSIFIER.classify(text, filename)
    else:
        # Fallback wenn Router nicht lädt
        return {"category": "Sonstiges", "confidence": 0.6, "_error": "router_fail"}


def send_telegram_alert(message: str):
    """Sende Telegram Benachrichtigung."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"  📱 [TELEGRAM DISABLED] {message}")
        return
    
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
    except Exception as e:
        print(f"  ⚠️ Telegram Fehler: {e}")

def save_to_shadow_ledger(data: Dict[str, Any]):
    """Speichere Datei-Metadaten in Shadow Ledger."""
    conn = sqlite3.connect(SHADOW_LEDGER_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO files 
        (sha256, original_filename, current_filename, original_path, 
         current_path, file_size, mime_type, category, subcategory,
         confidence, extracted_text, meta_description, tags, status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("sha256"),
        data.get("original_filename"),
        data.get("current_filename", data.get("original_filename")),
        data.get("original_path"),
        data.get("current_path"),
        data.get("file_size"),
        data.get("mime_type"),
        data.get("category"),
        data.get("subcategory"),
        data.get("confidence"),
        data.get("extracted_text", "")[:50000],
        data.get("meta_description"),
        json.dumps(data.get("tags", [])),
        data.get("status", "indexed"),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()

def generate_embedding(text: str) -> Optional[List[float]]:
    """Generiere Embedding via Ollama."""
    if not text:
        return None
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={
                "model": "nomic-embed-text",
                "prompt": text[:8000]
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("embedding")
    except Exception as e:
        print(f"  ⚠️ Embedding Fehler: {e}")
    return None

def index_to_qdrant(doc_id: str, vector: List[float], payload: Dict[str, Any]) -> bool:
    """Indexiere Dokument in Qdrant."""
    headers = {"api-key": QDRANT_KEY} if QDRANT_KEY else {}
    response = requests.put(
        f"{QDRANT_URL}/collections/neural_vault/points",
        headers=headers,
        json={
            "points": [
                {
                    "id": hash(doc_id) % (2**63),
                    "vector": vector,
                    "payload": payload
                }
            ]
        },
        timeout=30
    )
    return response.status_code == 200

def process_file(filepath: Path) -> bool:
    """
    Verarbeite eine einzelne Datei aus der Inbox.
    Returns: True wenn erfolgreich, False bei Fehler
    """
    print(f"\n{'='*60}")
    print(f"📁 Verarbeite: {filepath.name}")
    print(f"{'='*60}")
    
    try:
        # 1. Basis-Analyse
        print("  1️⃣ Basis-Analyse...")
        stats = filepath.stat()
        file_hash = sha256_hash(filepath)
        mime_type = get_mime_type(filepath)

        # Enhanced: Dateityp via Magic Bytes erkennen
        file_type_info = None
        if ENHANCED_EXTRACTION_AVAILABLE:
            file_type_info = detect_file_type(filepath)
            print(f"     → Erkannt: {file_type_info.extension} ({file_type_info.detection_method})")

        data = {
            "sha256": file_hash,
            "original_filename": filepath.name,
            "original_path": str(filepath),
            "file_size": stats.st_size,
            "mime_type": mime_type,
            "extension": filepath.suffix.lower(),
            "file_created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "file_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        }

        # Magic Detection überschreibt Extension-basierte Info
        if file_type_info and file_type_info.detection_method in ["magic", "container"]:
            data["detected_extension"] = f".{file_type_info.extension}"
            data["detected_category"] = file_type_info.category
        
        # 2. Text-Extraktion (Unified Service mit Docling-First Routing)
        print("  2️⃣ Text-Extraktion...")
        ext = filepath.suffix.lower()

        # Unified Extraction Service (Docling-First Strategie)
        # Benchmark: Docling 97.9% vs Tika 75% auf Tables
        if UNIFIED_EXTRACTION_AVAILABLE and is_enabled("USE_PARSER_ROUTING"):
            parser = get_parser(ext)
            print(f"     ℹ️ Parser Routing: {parser.value}")

            extraction_result = unified_extract(filepath)

            if extraction_result.success:
                data["extracted_text"] = extraction_result.text
                data["extraction_source"] = extraction_result.source
                data["extraction_confidence"] = extraction_result.confidence
                data["extended_metadata"] = extraction_result.metadata

                fallback_info = " (Fallback)" if extraction_result.fallback_used else ""
                print(f"     ✅ {extraction_result.source}{fallback_info}: {extraction_result.char_count} chars")

                if extraction_result.fallback_used:
                    data["fallback_used"] = True
                    data["original_parser"] = extraction_result.metadata.get("original_parser", "unknown")
            else:
                data["extracted_text"] = ""
                data["extraction_source"] = extraction_result.source
                data["extraction_error"] = extraction_result.original_error
                print(f"     ⚠️ Extraction failed: {extraction_result.original_error}")

        # Legacy: Extended Processors
        elif EXTENDED_AVAILABLE and ext in EXTENDED_EXTENSIONS:
            ext_result = process_extended_file(filepath)
            if ext_result.success:
                data["extracted_text"] = ext_result.extracted_text
                data["extended_metadata"] = ext_result.metadata
                data["extraction_source"] = "extended_processor"
                print(f"     → Extended Processor: {ext_result.summary}")
            else:
                data["extracted_text"] = ""
                data["extraction_error"] = ext_result.error

        # ABT-N02: Data Narrator für Tabellen
        elif DATA_NARRATOR_AVAILABLE and is_enabled("USE_DATA_NARRATOR") and ext in {".csv", ".xlsx", ".xls"}:
            print("     ℹ️ Data Narrator aktiv...")
            try:
                if ext == ".csv":
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)

                narrative = narrate_table(df, str(filepath))
                data["extracted_text"] = narrative
                data["extraction_source"] = "data_narrator"
                print("     ✅ Narrative generiert")
            except Exception as e:
                print(f"     ⚠️ Data Narrator Fehler: {e}, Fallback auf Tika")
                text = extract_text_tika(filepath)
                data["extracted_text"] = text or ""
                data["extraction_source"] = "tika_fallback"

        # Legacy ABT-B04: Docling nur für PDFs (vor Unified Service)
        elif DOCLING_AVAILABLE and is_enabled("USE_DOCLING_PDF") and ext == ".pdf":
            print("     ℹ️ Docling Deep Extract aktiv...")
            try:
                docling_service = DeepIngestService()
                md_content, meta = docling_service.process_file(str(filepath))

                data["extracted_text"] = md_content
                data["extraction_source"] = "docling"
                data["extended_metadata"] = meta
                print(f"     ✅ Docling Extract: {len(md_content)} chars")
            except Exception as e:
                print(f"     ⚠️ Docling Fehler: {e}, Fallback auf Tika")
                text = extract_text_tika(filepath)
                data["extracted_text"] = text or ""
                data["extraction_source"] = "tika_fallback"

        elif ext in TEXT_EXTENSIONS:
            text = extract_text_tika(filepath)
            data["extracted_text"] = text or ""
            data["extraction_source"] = "tika"
        else:
            data["extracted_text"] = ""
            data["extraction_source"] = "none"
        
        # ABT-B06: PII Masking anwenden
        if data.get("extracted_text"):
             data["extracted_text"] = mask_sensitive_data(data["extracted_text"])

        # 3. KI-Klassifizierung
        print("  3️⃣ KI-Klassifizierung...")
        classification = classify_with_ollama(
            data.get("extracted_text", filepath.name),
            filepath.name
        )
        data.update(classification)
        
        # 4. Smart Filename generieren
        print("  4️⃣ Filename generieren...")
        new_filename = generate_smart_filename(
            filepath.name,
            data.get("category", "Sonstiges"),
            data.get("entity", ""),
            data.get("date", "")
        )
        data["new_filename"] = new_filename
        
        # 5. Zielordner bestimmen
        target_folder = determine_target_folder(
            data.get("category", "Sonstiges"),
            data.get("subcategory", "")
        )
        data["target_folder"] = target_folder
        
        # 6. Quality Gates
        print("  5️⃣ Quality Gates...")
        qr = run_quality_gates(data)
        
        for gate in qr.gates:
            icon = "✅" if gate.passed else "❌"
            print(f"      {icon} {gate.gate_name}")
        
        if not qr.passed:
            # Quarantäne
            print(f"  ❌ Quality Gates FEHLGESCHLAGEN")
            print(f"     Grund: {qr.quarantine_reason}")
            
            quarantine_path = Path(qr.quarantine_folder) / filepath.name
            shutil.move(str(filepath), str(quarantine_path))
            
            data["current_path"] = str(quarantine_path)
            data["current_filename"] = filepath.name
            data["status"] = "quarantined"
            save_to_shadow_ledger(data)
            
            send_telegram_alert(
                f"⚠️ *Datei in Quarantäne*\n"
                f"📄 `{filepath.name}`\n"
                f"❌ {qr.quarantine_reason}\n"
                f"📁 {qr.quarantine_folder}"
            )
            return False
        
        # 7. Datei verschieben
        print("  6️⃣ Datei verschieben...")
        Path(target_folder).mkdir(parents=True, exist_ok=True)
        target_path = Path(target_folder) / new_filename
        shutil.move(str(filepath), str(target_path))
        
        data["current_path"] = str(target_path)
        data["current_filename"] = new_filename
        data["status"] = "indexed"
        
        # 8. Shadow Ledger speichern
        print("  7️⃣ Shadow Ledger speichern...")
        save_to_shadow_ledger(data)
        
        # 9. Qdrant indexieren
        print("  8️⃣ Qdrant indexieren...")
        qdrant_payload = {
            "id": file_hash,
            "original_filename": data["original_filename"],
            "current_filename": new_filename,
            "current_path": str(target_path),
            "category": data.get("category"),
            "subcategory": data.get("subcategory"),
            "meta_description": data.get("meta_description"),
            "extracted_text": data.get("extracted_text", "")[:50000],
            "tags": data.get("tags", []),
            "confidence": data.get("confidence", 0),
            "indexed_at": datetime.now().isoformat(),
            # Pattern-of-Life Felder
            "extension": data.get("extension"),
            "file_created": data.get("file_created"),
            "file_modified": data.get("file_modified"),
            "mime_type": data.get("mime_type"),
        }

        embedding_text = qdrant_payload.get("extracted_text") or qdrant_payload.get("meta_description", "")
        vector = generate_embedding(embedding_text)
        if not vector:
            raise RuntimeError("Kein Embedding erzeugt")

        qdrant_payload["file_path"] = qdrant_payload.pop("current_path", "")
        index_to_qdrant(qdrant_payload["id"], vector, qdrant_payload)
        
        print(f"\n  ✅ ERFOLGREICH!")
        print(f"     Von: {filepath.name}")
        print(f"     Nach: {target_path}")
        print(f"     Kategorie: {data.get('category')} ({data.get('confidence', 0):.0%})")
        
        return True
        
    except Exception as e:
        print(f"\n  ❌ FEHLER: {e}")
        
        # In Quarantäne verschieben
        error_path = QUARANTINE_BASE / "_processing_error" / filepath.name
        try:
            shutil.move(str(filepath), str(error_path))
        except:
            pass
        
        send_telegram_alert(
            f"🔴 *Verarbeitungsfehler*\n"
            f"📄 `{filepath.name}`\n"
            f"❌ {str(e)[:200]}"
        )
        return False

class InboxHandler(FileSystemEventHandler):
    """Watchdog Handler für Inbox-Überwachung."""
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        
        # Kurz warten bis Datei vollständig geschrieben
        time.sleep(2)
        
        if filepath.exists():
            process_file(filepath)

def run_once():
    """Verarbeite alle Dateien in der Inbox einmal."""
    print("🚀 Smart Ingestion - Einmaliger Durchlauf")
    print("-" * 60)
    
    files = list(INBOX_PATH.glob("*"))
    files = [f for f in files if f.is_file()]
    
    if not files:
        print("📭 Inbox ist leer - keine Dateien zu verarbeiten")
        return
    
    print(f"📥 {len(files)} Datei(en) in der Inbox\n")
    
    success = 0
    errors = 0
    
    for filepath in files:
        if process_file(filepath):
            success += 1
        else:
            errors += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Fertig! Erfolg: {success}, Fehler: {errors}")

def run_watch():
    """Überwache Inbox kontinuierlich."""
    print("👁️ Smart Ingestion - Überwachungsmodus")
    print(f"📁 Beobachte: {INBOX_PATH}")
    print("-" * 60)
    print("Warte auf neue Dateien... (Strg+C zum Beenden)\n")
    
    observer = Observer()
    observer.schedule(InboxHandler(), str(INBOX_PATH), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n👋 Überwachung beendet")
    
    observer.join()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Neural Vault Smart Ingestion")
    parser.add_argument("--watch", action="store_true", help="Kontinuierlich überwachen")
    parser.add_argument("--once", action="store_true", help="Einmal durchlaufen")
    args = parser.parse_args()
    
    # Shadow Ledger initialisieren
    init_shadow_ledger()
    
    if args.watch:
        run_watch()
    else:
        run_once()

if __name__ == "__main__":
    main()
