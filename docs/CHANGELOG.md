# Changelog
## Neural Vault / Conductor

Alle wichtigen Änderungen am Projekt werden hier dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/)
und [Semantic Versioning](https://semver.org/lang/de/).

---

## [Unreleased]

### Geplant (PROPOSED)
- **ABT-R02:** GLiNER-Klassifikation statt Ollama LLM ([ADR-010](ADR/ADR-010-classification-method.md))
- **ABT-B01:** Cross-Encoder Reranking für Suche ([ADR-015](ADR/ADR-015-search-reranking.md))
- **ABT-N01:** Entity Resolution mit Fuzzy Matching ([ADR-020](ADR/ADR-020-entity-resolution.md))
- **ABT-N02:** Data Narrator für Tabellen ([ADR-021](ADR/ADR-021-data-narrator.md))

### In Test (EXPERIMENTAL)
- `neural-worker` Docker Container mit Docling + GLiNER
- LanceDB als "Neural Spine" für Archiv-Vektoren
- Perplexica UI integration

### Deprecated
- Ollama LLM für Klassifikation (zu langsam)
- Tesseract OCR (ersetzt durch Docling)
- Auto-Rename von Dateien (ersetzt durch Metadata-Layer)
- Graph-Visualisierung (ersetzt durch Related Documents)

---

## [2.0.0] - 2025-12-28

### Hinzugefügt
- **A/B-Test-Framework** basierend auf Erfolgsalgorithmus ([AB_TEST_FRAMEWORK.md](AB_TEST_FRAMEWORK.md))
- **15 neue ADRs** (ADR-009 bis ADR-023) für Architektur-Entscheidungen
- **Feature Lifecycle Management** ([FEATURE_LIFECYCLE.md](FEATURE_LIFECYCLE.md))
- **Component Status Registry** ([COMPONENT_STATUS.md](COMPONENT_STATUS.md))
- Konsolidierte Analyse aus Claude Opus 4.5 + Gemini 3 Pro

### Geändert
- Dokumentationsstandard erweitert um Status-Tracking
- ADR-Template um Supersedes/Superseded-Felder erweitert

### Analyse-Ergebnisse
- 6 RED Buttons identifiziert (zu eliminieren)
- 6 BLUE Buttons identifiziert (zu verstärken)
- 4 NEW Features vorgeschlagen (zu evaluieren)

---

## [1.5.0] - 2025-12-26

### Hinzugefügt
- **neural-worker** Docker Container
  - Docling für Deep PDF Parsing
  - GLiNER für Named Entity Recognition
  - LanceDB für lokale Vektorspeicherung
- **Audit-Dokument** ([AUDIT_2025-12-26.md](AUDIT_2025-12-26.md))

### Geändert
- docker-compose.yml um neural-worker erweitert
- Volumes für huggingface_cache und lancedb_data

---

## [1.4.0] - 2025-12-20

### Hinzugefügt
- **Quality Gates** in `smart_ingest.py`
  - 6 automatische Prüfungen vor File-Move
  - Quarantäne-System für unsichere Dateien
- **Shadow Ledger** für Datei-Tracking
- **Hybrid Search** (BM25 + Vektor) via Qdrant

### Dokumentation
- ADR-007: File Processing Quality

---

## [1.3.0] - 2025-12-15

### Hinzugefügt
- **Nextcloud Integration** für Remote-Zugriff
- **Whisper Container** für Audio-Transkription
- **FFmpeg Container** für Media-Processing

### Dokumentation
- ADR-006: Nextcloud Integration
- RUNBOOK-001: Nextcloud Setup

---

## [1.2.0] - 2025-12-10

### Hinzugefügt
- **Knowledge Graph** mit rustworkx
- **Topic Modeling** mit BERTopic
- **Graph Explorer** in Gradio UI

---

## [1.1.0] - 2025-12-05

### Hinzugefügt
- **Smart Ingest Pipeline**
  - Watchdog für `_Inbox` Ordner
  - Tika für Textextraktion
  - Ollama für Klassifikation
- **Batch Processor** für Massenverarbeitung

---

## [1.0.0] - 2025-12-01

### Initialer Release
- Docker Compose Stack mit Basis-Services
  - PostgreSQL, Redis, n8n
  - Qdrant, Tika, Ollama
- Basis-Dokumentation
  - VISION.md, DOCUMENTATION_STANDARD.md
  - Erste ADRs (001-005)

---

## Version-Konventionen

- **MAJOR:** Inkompatible Änderungen, Breaking Changes
- **MINOR:** Neue Features, rückwärtskompatibel
- **PATCH:** Bugfixes, kleine Verbesserungen

### Beispiele

| Änderung | Version-Bump |
|----------|--------------|
| GLiNER ersetzt Ollama komplett | MAJOR (Breaking) |
| Neues Feature: Data Narrator | MINOR |
| Bugfix in Quality Gates | PATCH |
| Neue Dokumentation | Kein Bump |

---

## Migration Guides

Bei MAJOR-Updates werden Migrations-Anleitungen erstellt:

| Von | Nach | Guide |
|-----|------|-------|
| 1.x | 2.x | (Noch nicht erforderlich) |

---

*Dieses Changelog wird bei jedem Release aktualisiert.*
