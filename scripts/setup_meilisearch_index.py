"""
Neural Vault Meilisearch Index Setup
====================================

Konfiguriert den Meilisearch-Index mit optimierten Einstellungen für:
- Zeitstempel-basierte Filter (Pattern-of-Life Analyse)
- Facettierte Suche nach Kategorie, Typ, Datum
- Typo-Toleranz für deutsche Dokumente

Übernahme aus Gemini-Analyse vom 2025-12-28:
"Pattern-of-Life Analyse: Zeitstempel wären wichtiger als Inhalte."

Usage:
    python setup_meilisearch_index.py
    python setup_meilisearch_index.py --reset  # Index neu erstellen
"""

import requests
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.paths import MEILISEARCH_URL, BASE_DIR

# Environment laden
def load_env() -> Dict[str, str]:
    env_path = BASE_DIR / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
    return env

ENV = load_env()
MEILI_KEY = ENV.get("MEILI_MASTER_KEY", "")

# Index-Konfiguration
INDEX_NAME = "files"

# Felder, die durchsuchbar sein sollen (Reihenfolge = Priorität)
SEARCHABLE_ATTRIBUTES = [
    "original_filename",
    "current_filename",
    "extracted_text",
    "meta_description",
    "tags",
    "category",
    "subcategory",
    "entities_flat"  # Flache Darstellung der Entities für Suche
]

# Felder, die gefiltert werden können
FILTERABLE_ATTRIBUTES = [
    "category",
    "subcategory",
    "extension",
    "mime_type",
    "file_created_timestamp",    # Unix Timestamp für Range-Filter
    "file_modified_timestamp",   # Unix Timestamp für Range-Filter
    "indexed_at_timestamp",      # Unix Timestamp für Range-Filter
    "file_size",
    "confidence",
    "status",
    "source_type",               # pdf, audio, video, etc.
    "year_created",              # Für schnelle Jahr-Filter
    "month_created",             # Für schnelle Monat-Filter
    "weekday_created",           # Mo=0, So=6 für Wochentag-Analyse
    "hour_created"               # Für Tageszeit-Analyse
]

# Felder, die sortiert werden können
SORTABLE_ATTRIBUTES = [
    "file_created_timestamp",
    "file_modified_timestamp",
    "indexed_at_timestamp",
    "file_size",
    "confidence",
    "original_filename"
]

# Felder, die in der Antwort angezeigt werden
DISPLAYED_ATTRIBUTES = [
    "id",
    "original_filename",
    "current_filename",
    "current_path",
    "category",
    "subcategory",
    "confidence",
    "meta_description",
    "tags",
    "file_size",
    "file_created",
    "file_modified",
    "extension",
    "source_type"
]

# Ranking-Regeln (Reihenfolge = Priorität)
RANKING_RULES = [
    "words",           # Anzahl der gefundenen Wörter
    "typo",            # Weniger Typos = besser
    "proximity",       # Wörter näher beieinander = besser
    "attribute",       # Höhere Attribute-Priorität = besser
    "sort",            # User-definierte Sortierung
    "exactness",       # Exakte Matches = besser
    "confidence:desc"  # Höhere KI-Konfidenz = besser
]

# Typo-Toleranz Einstellungen
TYPO_TOLERANCE = {
    "enabled": True,
    "minWordSizeForTypos": {
        "oneTypo": 4,    # Ab 4 Zeichen: 1 Typo erlaubt
        "twoTypos": 8    # Ab 8 Zeichen: 2 Typos erlaubt
    },
    "disableOnWords": [],
    "disableOnAttributes": ["id", "sha256", "extension"]
}

# Synonyme für deutsche Dokumente
SYNONYMS = {
    "rechnung": ["invoice", "bill", "beleg"],
    "vertrag": ["contract", "agreement", "kontrakt"],
    "foto": ["photo", "bild", "image"],
    "video": ["film", "clip", "aufnahme"],
    "email": ["e-mail", "mail", "nachricht"],
    "dokument": ["document", "datei", "file"]
}


class MeilisearchSetup:
    """Konfiguriert den Meilisearch-Index."""

    def __init__(self, url: str = None, api_key: str = None):
        self.url = url or MEILISEARCH_URL
        self.api_key = api_key or MEILI_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def check_health(self) -> bool:
        """Prüft, ob Meilisearch erreichbar ist."""
        try:
            response = requests.get(f"{self.url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Meilisearch nicht erreichbar: {e}")
            return False

    def get_index_stats(self) -> Optional[Dict]:
        """Holt Statistiken des Index."""
        try:
            response = requests.get(
                f"{self.url}/indexes/{INDEX_NAME}/stats",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"⚠️ Fehler beim Abrufen der Stats: {e}")
        return None

    def create_index(self) -> bool:
        """Erstellt den Index (falls nicht vorhanden)."""
        try:
            response = requests.post(
                f"{self.url}/indexes",
                headers=self.headers,
                json={
                    "uid": INDEX_NAME,
                    "primaryKey": "id"
                },
                timeout=10
            )
            if response.status_code in (200, 201, 202):
                print(f"✅ Index '{INDEX_NAME}' erstellt oder existiert bereits")
                return True
            elif response.status_code == 409:
                print(f"ℹ️ Index '{INDEX_NAME}' existiert bereits")
                return True
            else:
                print(f"⚠️ Index-Erstellung: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Fehler bei Index-Erstellung: {e}")
            return False

    def delete_index(self) -> bool:
        """Löscht den Index."""
        try:
            response = requests.delete(
                f"{self.url}/indexes/{INDEX_NAME}",
                headers=self.headers,
                timeout=10
            )
            if response.status_code in (200, 202, 204):
                print(f"🗑️ Index '{INDEX_NAME}' gelöscht")
                return True
            else:
                print(f"⚠️ Index-Löschung: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Fehler beim Löschen: {e}")
            return False

    def configure_settings(self) -> bool:
        """Konfiguriert alle Index-Einstellungen."""
        settings = {
            "searchableAttributes": SEARCHABLE_ATTRIBUTES,
            "filterableAttributes": FILTERABLE_ATTRIBUTES,
            "sortableAttributes": SORTABLE_ATTRIBUTES,
            "displayedAttributes": DISPLAYED_ATTRIBUTES,
            "rankingRules": RANKING_RULES,
            "typoTolerance": TYPO_TOLERANCE,
            "synonyms": SYNONYMS
        }

        try:
            response = requests.patch(
                f"{self.url}/indexes/{INDEX_NAME}/settings",
                headers=self.headers,
                json=settings,
                timeout=30
            )
            if response.status_code in (200, 202):
                print("✅ Index-Einstellungen konfiguriert")
                return True
            else:
                print(f"⚠️ Settings: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Fehler bei Settings: {e}")
            return False

    def wait_for_task(self, task_uid: int, timeout: int = 60) -> bool:
        """Wartet auf Abschluss eines Tasks."""
        import time
        start = time.time()

        while time.time() - start < timeout:
            try:
                response = requests.get(
                    f"{self.url}/tasks/{task_uid}",
                    headers=self.headers,
                    timeout=10
                )
                if response.status_code == 200:
                    task = response.json()
                    if task.get("status") == "succeeded":
                        return True
                    elif task.get("status") == "failed":
                        print(f"❌ Task fehlgeschlagen: {task.get('error')}")
                        return False
            except Exception:
                pass
            time.sleep(1)

        print("⚠️ Timeout beim Warten auf Task")
        return False

    def setup(self, reset: bool = False) -> bool:
        """Führt das komplette Setup durch."""
        print("=" * 60)
        print("🔧 Neural Vault Meilisearch Setup")
        print("=" * 60)
        print()

        # Health Check
        print("1️⃣ Prüfe Meilisearch-Verbindung...")
        if not self.check_health():
            return False
        print(f"   ✅ Verbunden mit {self.url}")
        print()

        # Reset wenn angefordert
        if reset:
            print("2️⃣ Lösche bestehenden Index...")
            self.delete_index()
            print()

        # Index erstellen
        print("3️⃣ Erstelle Index...")
        if not self.create_index():
            return False
        print()

        # Settings konfigurieren
        print("4️⃣ Konfiguriere Index-Einstellungen...")
        print(f"   - Durchsuchbare Felder: {len(SEARCHABLE_ATTRIBUTES)}")
        print(f"   - Filterbare Felder: {len(FILTERABLE_ATTRIBUTES)}")
        print(f"   - Sortierbare Felder: {len(SORTABLE_ATTRIBUTES)}")
        print(f"   - Synonyme: {len(SYNONYMS)} Gruppen")
        if not self.configure_settings():
            return False
        print()

        # Stats ausgeben
        print("5️⃣ Index-Statistiken:")
        stats = self.get_index_stats()
        if stats:
            print(f"   - Dokumente: {stats.get('numberOfDocuments', 0)}")
            print(f"   - Indexiert: {stats.get('isIndexing', False)}")
        print()

        print("=" * 60)
        print("✅ Setup abgeschlossen!")
        print("=" * 60)
        print()
        print("📋 Filterbare Zeitstempel-Felder:")
        print("   - file_created_timestamp (Unix)")
        print("   - file_modified_timestamp (Unix)")
        print("   - year_created, month_created")
        print("   - weekday_created (0=Mo, 6=So)")
        print("   - hour_created (0-23)")
        print()
        print("📋 Beispiel-Abfragen:")
        print('   filter: "year_created = 2024"')
        print('   filter: "weekday_created = 6"  # Sonntags erstellt')
        print('   filter: "hour_created >= 22"   # Nachts erstellt')
        print('   filter: "file_created_timestamp > 1704067200"  # Nach 2024-01-01')
        print()

        return True


def prepare_document_for_index(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bereitet ein Dokument für die Indexierung vor.

    Fügt berechnete Zeitstempel-Felder hinzu für Pattern-of-Life Analyse.
    """
    result = doc.copy()

    # Zeitstempel aus ISO-Strings berechnen
    for field, ts_field in [
        ("file_created", "file_created_timestamp"),
        ("file_modified", "file_modified_timestamp"),
        ("indexed_at", "indexed_at_timestamp")
    ]:
        if field in doc and doc[field]:
            try:
                dt = datetime.fromisoformat(doc[field].replace("Z", "+00:00"))
                result[ts_field] = int(dt.timestamp())

                # Zusätzliche Felder für Pattern-Analyse
                if field == "file_created":
                    result["year_created"] = dt.year
                    result["month_created"] = dt.month
                    result["weekday_created"] = dt.weekday()  # 0=Montag, 6=Sonntag
                    result["hour_created"] = dt.hour
            except Exception:
                pass

    # Entities flatten für Suche
    if "entities" in doc and isinstance(doc["entities"], dict):
        flat_parts = []
        for key, value in doc["entities"].items():
            if isinstance(value, list):
                flat_parts.extend([str(v) for v in value])
            elif value:
                flat_parts.append(str(value))
        result["entities_flat"] = " ".join(flat_parts)

    # Source Type aus Extension ableiten
    if "extension" in doc:
        ext = doc["extension"].lower().lstrip(".")
        type_mapping = {
            "pdf": "pdf",
            "docx": "document", "doc": "document", "txt": "document",
            "xlsx": "spreadsheet", "xls": "spreadsheet", "csv": "spreadsheet",
            "jpg": "image", "jpeg": "image", "png": "image",
            "mp3": "audio", "wav": "audio", "m4a": "audio",
            "mp4": "video", "mkv": "video", "avi": "video",
            "eml": "email", "msg": "email"
        }
        result["source_type"] = type_mapping.get(ext, "other")

    return result


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Meilisearch Index Setup")
    parser.add_argument("--reset", action="store_true", help="Index zurücksetzen")
    parser.add_argument("--stats", action="store_true", help="Nur Stats anzeigen")
    args = parser.parse_args()

    setup = MeilisearchSetup()

    if args.stats:
        if setup.check_health():
            stats = setup.get_index_stats()
            if stats:
                print(json.dumps(stats, indent=2))
            else:
                print("Keine Stats verfügbar")
        sys.exit(0)

    success = setup.setup(reset=args.reset)
    sys.exit(0 if success else 1)
