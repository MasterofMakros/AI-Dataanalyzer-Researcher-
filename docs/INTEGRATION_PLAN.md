# Integration Plan: Was einbinden, was nicht

> Pragmatische Integration der neuen Komponenten
> Stand: 29.12.2025

---

## Übersicht: Was einbinden?

| Komponente | Einbinden? | Priorität | Aufwand | Begründung |
|:-----------|:-----------|:----------|:--------|:-----------|
| **format_registry.py** | ✅ JA | P0 | Niedrig | Zentrale MIME-Erkennung |
| **Magic Byte Detection** | ✅ JA | P0 | Niedrig | Robustere Dateierkennung |
| **context_header.py** | ✅ JA | P1 | Bereits da | RAG-Qualität verbessern |
| **feedback_tracker.py** | ✅ JA | P1 | Bereits da | Lernfähigkeit |
| **tika_markdown.py** | ✅ JA | P1 | Bereits da | Tabellenerhalt |
| **Universal Router** | ⚠️ OPTIONAL | P2 | Mittel | Nur bei >10k Dateien |
| **Orchestrator** | ⚠️ OPTIONAL | P3 | Hoch | Nur bei Skalierung |
| **Extraction Workers** | ❌ NEIN | - | Hoch | Überflüssig, existiert |
| **docker-compose.intelligence.yml** | ❌ NEIN | - | - | Zu komplex für Start |

---

## Phase 1: Sofort einbinden (Tag 1)

### 1.1 Format Registry in smart_ingest.py integrieren

Die Format Registry ersetzt die hardgecodeten Extension-Listen:

```python
# ALT (in smart_ingest.py):
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.xlsx', ...]

# NEU:
from config.format_registry import get_format_spec, get_all_supported_extensions

SUPPORTED_EXTENSIONS = get_all_supported_extensions()
```

### 1.2 Magic Byte Detection hinzufügen

Statt nur auf Extensions zu vertrauen:

```python
# In smart_ingest.py oder als separate Funktion:

from config.format_registry import FORMAT_REGISTRY

def detect_file_type(filepath: Path) -> tuple[str, str]:
    """Erkennt Dateityp über Magic Bytes + Extension."""

    # 1. Magic Bytes prüfen
    try:
        with open(filepath, 'rb') as f:
            header = f.read(32)

        MAGIC_SIGNATURES = {
            b"%PDF": "pdf",
            b"PK\x03\x04": "zip_based",
            b"\xd0\xcf\x11\xe0": "ole2",
            b"\xff\xd8\xff": "jpg",
            b"\x89PNG": "png",
            b"ID3": "mp3",
            b"fLaC": "flac",
            b"RIFF": "riff",
            b"OggS": "ogg",
        }

        for magic, ext in MAGIC_SIGNATURES.items():
            if header.startswith(magic):
                return ext, "magic"
    except Exception:
        pass

    # 2. Extension Fallback
    ext = filepath.suffix.lower().lstrip('.')
    return ext, "extension"
```

### 1.3 Tika HTML→Markdown aktivieren

In `smart_ingest.py` die Tika-Extraktion ersetzen:

```python
# ALT:
def extract_with_tika(filepath):
    response = requests.put(TIKA_URL, data=f, headers={"Accept": "text/plain"})
    return response.text

# NEU:
from scripts.utils.tika_markdown import extract_markdown

def extract_with_tika(filepath):
    return extract_markdown(filepath)  # Behält Tabellen!
```

---

## Phase 2: Bald einbinden (Woche 1)

### 2.1 Context Headers für RAG

Bei der Chunk-Erstellung Headers hinzufügen:

```python
from scripts.utils.context_header import create_chunk_for_rag

# Bei der Indexierung:
def prepare_for_index(doc: dict) -> dict:
    if doc.get('extracted_text'):
        doc['extracted_text'] = create_chunk_for_rag(
            text=doc['extracted_text'],
            filename=doc['original_filename'],
            category=doc.get('category'),
            confidence=doc.get('confidence')
        )
    return doc
```

### 2.2 Feedback Tracking aktivieren

Wenn User Dateien manuell umkategorisiert:

```python
from scripts.utils.feedback_tracker import FeedbackTracker

tracker = FeedbackTracker()

# Bei manueller Korrektur (z.B. über UI):
def on_user_correction(file_hash, old_category, new_category):
    tracker.log_correction(
        file_hash=file_hash,
        filename=filename,
        predicted_category=old_category,
        actual_category=new_category
    )
```

## Phase 3: Später einbinden (Wenn nötig)

### 3.1 Universal Router (nur bei Performance-Problemen)

**Wann einbinden:**
- Mehr als 10.000 Dateien zu verarbeiten
- Batch-Processing benötigt
- Dateityp-Erkennung zu langsam

**Wie einbinden:**
```bash
# Als separater Service starten
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.intelligence.yml up -d universal-router

# In smart_ingest.py:
def route_file(filepath):
    response = requests.post(
        "http://localhost:8030/route",
        json={"filepath": str(filepath)}
    )
    return response.json()
```

### 3.2 Orchestrator (nur bei Skalierung)

**Wann einbinden:**
- Mehrere Worker parallel laufen sollen
- Priority-basierte Verarbeitung benötigt
- >100.000 Dateien im Backlog

**NICHT einbinden wenn:**
- Einzelner Laptop/PC
- <10.000 Dateien
- Keine Eile bei Verarbeitung

---

## Was NICHT einbinden

### ❌ docker-compose.intelligence.yml

**Warum nicht:**
- Zu viele Services (20+)
- Hoher RAM-Verbrauch (~25 GB)
- Komplexität vs. Nutzen schlecht
- Bestehende docker-compose.yml funktioniert

**Stattdessen:** Bestehende docker-compose.yml weiter nutzen, einzelne Services bei Bedarf hinzufügen.

### ❌ Spezialisierte Extraction Workers

**Warum nicht:**
- Dupliziert bestehende Logik in smart_ingest.py
- Zusätzliche Komplexität
- Mehr Container = mehr Wartung

**Stattdessen:** Die Worker-Logik als Referenz nutzen, aber in smart_ingest.py integrieren.

### ❌ Redis Streams (vorerst)

**Warum nicht:**
- Overhead für kleines Setup
- SQLite-Queue reicht für <50.000 Dateien
- Debugging komplexer

**Wann doch:** Bei echter horizontaler Skalierung.

---

## Konkrete Änderungen an smart_ingest.py

### Minimale Integration (empfohlen):

```python
# Am Anfang der Datei hinzufügen:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.format_registry import get_format_spec, FORMAT_REGISTRY
from scripts.utils.tika_markdown import extract_markdown
from scripts.utils.context_header import create_chunk_for_rag
from scripts.utils.feedback_tracker import FeedbackTracker

# Globale Instanzen
feedback_tracker = FeedbackTracker()

# Ersetze SUPPORTED_EXTENSIONS:
SUPPORTED_EXTENSIONS = [f".{ext}" for ext in FORMAT_REGISTRY.keys() if ext != "*"]

# In extract_text_content():
def extract_text_content(filepath: Path) -> str:
    """Extrahiert Text - jetzt mit Markdown-Erhalt."""
    spec = get_format_spec(filepath.suffix)

    if spec.processor.value in ["tika", "tika_html"]:
        # Tika mit HTML→Markdown für Tabellenerhalt
        return extract_markdown(filepath)

    # ... rest der Logik
```

---

## Empfohlene Reihenfolge

```
Tag 1:
├── format_registry.py in config/ (✓ bereits da)
├── SUPPORTED_EXTENSIONS ersetzen
└── Magic Byte Detection hinzufügen

Woche 1:
├── tika_markdown.py aktivieren
├── context_header.py bei Indexierung nutzen
└── feedback_tracker.py für UI vorbereiten

Später (wenn nötig):
├── Universal Router als Service
└── Priority Queues für Batch-Processing
```

---

## Dateien die NICHT ins Projekt sollen

Diese Dateien sind **Referenz/Dokumentation**, nicht für Produktion:

```
docker-compose.intelligence.yml  → Nur als Vorlage
docker/orchestrator/             → Nur bei Skalierung
docker/workers/                  → Referenz-Implementation
docker/universal-router/         → Optional, später
```

---

## Quick-Start: Minimale Integration

```bash
# 1. Format Registry testen
python -c "from config.format_registry import get_format_stats; print(get_format_stats())"

# 2. Tika Markdown testen
python -c "from scripts.utils.tika_markdown import extract_markdown; print(extract_markdown('test.pdf')[:500])"

# 3. smart_ingest.py mit neuen Imports starten
python scripts/smart_ingest.py --path /path/to/files
```

---

*Dokumentation: 29.12.2025*
