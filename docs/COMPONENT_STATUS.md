# Component Status Registry
## Aktueller Status aller Komponenten im Neural Vault

> **Zweck:** Single Source of Truth für den Status jeder Komponente.
> Verhindert Konflikte zwischen alten und neuen Implementierungen.

---

## Status-Legende

| Status | Symbol | Bedeutung |
|--------|--------|-----------|
| ACTIVE | 🟢 | Produktiv, empfohlen |
| EXPERIMENTAL | 🟡 | In A/B-Test, nicht für Produktion |
| DEPRECATED | 🟠 | Wird abgeschaltet, Alternative nutzen |
| PROPOSED | 🔵 | Geplant, nicht implementiert |
| REJECTED | 🔴 | Getestet und verworfen |

---

## Klassifikation & NER

| Komponente | Status | Version | Ersetzt durch | ADR |
|------------|--------|---------|---------------|-----|
| `smart_ingest.py` (Ollama) | 🔴 REMOVED | v1.0 | neural-worker GLiNER | [ADR-010](ADR/ADR-010-classification-method.md) |
| `neural-worker` (GLiNER) | 🟢 ACTIVE | v2.1 | - | [ADR-010](ADR/ADR-010-classification-method.md) |
| `pii_scanner.py` | 🟢 ACTIVE | v1.0 | - | - |

**Aktueller Standard:** `neural-worker` GLiNER
**Geplanter Standard:** -

---

## Dokument-Parsing

| Komponente | Status | Version | Ersetzt durch | ADR |
|------------|--------|---------|---------------|-----|
| Apache Tika (Docker) | 🟢 ACTIVE | v2.9 | Docling (für PDFs) | [ADR-018](ADR/ADR-018-pdf-parsing.md) |
| Docling (DeepIngest) | 🟢 ACTIVE | v1.0 | - | [ADR-018](ADR/ADR-018-pdf-parsing.md) |
| Tesseract OCR (Docker) | 🟠 DEPRECATED | v5.0 | Docling OCR | [ADR-005](ADR/ADR-005-ocr-strategy.md) |

**Aktueller Standard:** Hybrid (Docling für PDF, Tika für Rest)
**Geplanter Standard:** -

---

## Vector Database

| Komponente | Status | Version | Ersetzt durch | ADR |
|------------|--------|---------|---------------|-----|
| Qdrant (Docker) | 🟢 ACTIVE | v1.7 | LanceDB für Archiv | [ADR-019](ADR/ADR-019-vector-database.md) |
| LanceDB (neural-worker) | 🟡 EXPERIMENTAL | v0.4 | - | [ADR-019](ADR/ADR-019-vector-database.md) |

**Aktueller Standard:** Qdrant für alles
**Geplanter Standard:** Hybrid (Qdrant Hot, LanceDB Cold)

---

## Suche

| Komponente | Status | Version | Ersetzt durch | ADR |
|------------|--------|---------|---------------|-----|
| Meilisearch (BM25) | 🟢 ACTIVE | v1.6 | - | [ADR-008](ADR/ADR-008-hybrid-search.md) |
| Hybrid Search (BM25+Vektor) | 🟢 ACTIVE | v1.0 | - | [ADR-008](ADR/ADR-008-hybrid-search.md) |
| Cross-Encoder Reranking | 🔴 REJECTED | - | - | [ADR-015](ADR/ADR-015-search-reranking.md) |

**Aktueller Standard:** Hybrid Search ohne Reranking
**Geplanter Standard:** -

---

## Datei-Management

| Komponente | Status | Version | Ersetzt durch | ADR |
|------------|--------|---------|---------------|-----|
| Shadow Ledger (Event-basiert) | 🟠 DEPRECATED | v1.0 | Periodischer Scan | [ADR-009](ADR/ADR-009-shadow-ledger-tracking.md) |
| Periodischer Scan | 🔵 PROPOSED | - | - | [ADR-009](ADR/ADR-009-shadow-ledger-tracking.md) |
| Auto-Rename | 🟠 DEPRECATED | v1.0 | Metadata-Layer | [ADR-011](ADR/ADR-011-filename-strategy.md) |
| Metadata-Layer | 🔵 PROPOSED | - | - | [ADR-011](ADR/ADR-011-filename-strategy.md) |
| Quality Gates (50% Quarantäne) | 🟢 ACTIVE | v1.0 | 10% + Tags | [ADR-012](ADR/ADR-012-quarantine-threshold.md) |

---

## Knowledge Graph

| Komponente | Status | Version | Ersetzt durch | ADR |
|------------|--------|---------|---------------|-----|
| Graph Visualisierung | 🟠 DEPRECATED | v1.0 | Related Documents | [ADR-013](ADR/ADR-013-knowledge-graph-usage.md) |
| Entity Resolution (Exact) | 🟢 ACTIVE | v1.0 | Fuzzy Resolution | [ADR-020](ADR/ADR-020-entity-resolution.md) |
| Entity Resolution (Fuzzy) | 🔵 PROPOSED | - | - | [ADR-020](ADR/ADR-020-entity-resolution.md) |

---

## UI / Frontend

| Komponente | Status | Version | Ersetzt durch | ADR |
|------------|--------|---------|---------------|-----|
| Gradio Search UI | 🟢 ACTIVE | v1.0 | Evidence Board | [ADR-022](ADR/ADR-022-evidence-board-ui.md) |
| Evidence Board (React) | 🔵 PROPOSED | - | - | [ADR-022](ADR/ADR-022-evidence-board-ui.md) |
| Mission Control v2 | 🟡 EXPERIMENTAL | v0.1 | - | - |

---

## Docker Stack

| Service | Status | Profil | Ersetzt durch | ADR |
|---------|--------|--------|---------------|-----|
| postgres | 🟢 ACTIVE | core | - | - |
| redis | 🟢 ACTIVE | core | - | - |
| meilisearch | 🟢 ACTIVE | core | - | - |
| neural-worker | 🟢 ACTIVE | core | - | - |
| tika | 🟢 ACTIVE | core | Docling (teilweise) | [ADR-018](ADR/ADR-018-pdf-parsing.md) |
| n8n | 🟢 ACTIVE | core | - | - |
| qdrant | 🟢 ACTIVE | llm | LanceDB (teilweise) | [ADR-019](ADR/ADR-019-vector-database.md) |
| ollama | 🟢 ACTIVE | llm | - | [ADR-017](ADR/ADR-017-llm-backend.md) |
| whisper | 🟢 ACTIVE | media | - | - |
| nextcloud | 🟡 EXPERIMENTAL | sync | - | [ADR-006](ADR/ADR-006-nextcloud-integration.md) |
| tesseract-ocr | 🟠 DEPRECATED | - | Docling | [ADR-005](ADR/ADR-005-ocr-strategy.md) |
| ffmpeg-api | 🟠 DEPRECATED | - | Subprocess | [ADR-014](ADR/ADR-014-docker-stack-size.md) |
| sevenzip | 🟠 DEPRECATED | - | Subprocess | [ADR-014](ADR/ADR-014-docker-stack-size.md) |
| parser-service | 🟠 DEPRECATED | - | neural-worker | - |

---

## Neue Features (PROPOSED)

| Feature | Status | Priorität | ADR | Abhängigkeit |
|---------|--------|-----------|-----|--------------|
| Data Narrator | 🟢 ACTIVE | HOCH | [ADR-021](ADR/ADR-021-data-narrator.md) | neural-worker |
| Canary Tokens | 🔵 PROPOSED | NIEDRIG | [ADR-023](ADR/ADR-023-canary-tokens.md) | - |
| Evidence Board UI | 🔵 PROPOSED | MITTEL | [ADR-022](ADR/ADR-022-evidence-board-ui.md) | React, API |

---

## Feature Flags (Aktuell)

```python
FEATURE_FLAGS = {
    # Klassifikation
    "USE_GLINER_CLASSIFICATION": (True, "ACTIVE"),
    "USE_OLLAMA_CLASSIFICATION": (False, "REMOVED"),

    # Suche
    "ENABLE_RERANKING": (False, "REJECTED"),
    "USE_HYBRID_SEARCH": (True, "ACTIVE"),

    # Vector DB
    "USE_LANCEDB_ARCHIVE": (False, "EXPERIMENTAL"),
    "USE_QDRANT_ONLY": (True, "ACTIVE"),

    # Features
    "USE_DATA_NARRATOR": (True, "ACTIVE"),
    "USE_DOCLING_PDF": (True, "ACTIVE"),
    "USE_PII_MASKING": (True, "ACTIVE"),
}
```

---

## Konflikte & Lösungen

### Konflikt 1: Zwei Klassifikatoren aktiv

**Problem:**
- `smart_ingest.py` nutzt Ollama (DEPRECATED)
- `neural-worker` hat GLiNER (EXPERIMENTAL)
- Ergebnisse können unterschiedlich sein

**Lösung:**
1. Feature Flag `USE_GLINER_CLASSIFICATION` aktivieren
2. `smart_ingest.py` routet zu neural-worker
3. Ollama-Code in `deprecated/` verschieben

### Konflikt 2: Zwei Vector DBs

**Problem:**
- Qdrant enthält aktive Vektoren
- LanceDB enthält experimentelle Vektoren
- Suche findet nicht alles

**Lösung:**
1. Hybrid-Router implementieren (sucht in beiden)
2. Migration-Script: Qdrant → LanceDB für Archiv
3. Qdrant nur für Hot Data (letzte 30 Tage)

---

## Nächste Status-Änderungen (Geplant)

| Datum | Komponente | Von | Nach | Trigger |
|-------|------------|-----|------|---------|
| Nach ABT-R02 | GLiNER Klassifikation | EXPERIMENTAL | ACTIVE | A/B-Test bestanden |
| Nach ABT-R02 | Ollama Klassifikation | DEPRECATED | REMOVED | Migration abgeschlossen |
| Nach ABT-B01 | Cross-Encoder Reranking | PROPOSED | EXPERIMENTAL | Implementierung fertig |
| Nach ABT-B05 | LanceDB Hybrid | EXPERIMENTAL | ACTIVE | RAM-Test bestanden |

---

*Letzte Aktualisierung: 2025-12-28*
*Nächstes Review: Nach Abschluss der ersten A/B-Tests*
