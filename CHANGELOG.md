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
- Mission Control v2 React Dashboard

### Deprecated
- Ollama LLM für Klassifikation (zu langsam)
- Tesseract OCR (ersetzt durch Docling)
- Auto-Rename von Dateien (ersetzt durch Metadata-Layer)
- Graph-Visualisierung (ersetzt durch Related Documents)

---

## [2.1.6] - 2026-01-10

### Fixed
- **Surya OCR 0.17 API**: Complete rewrite for Surya 0.17+ compatibility.
  - Fixed predictor initialization: FoundationPredictor → RecognitionPredictor chain
  - Corrected API call: `rec(images, det_predictor=det)` replaces old detection-first pattern
  - All image formats (JPG, PNG, TIFF) now process successfully

## [2.1.5] - 2026-01-10

### Fixed
- **FFmpeg in Workers**: Replaced Docker-in-Docker with direct FFmpeg installation in worker containers.
- **Cross-Platform Paths**: Added `_translate_path()` for Windows/Linux/macOS volume mount compatibility.
- **VideoWorker**: Direct `ffmpeg`/`ffprobe` calls instead of `docker exec conductor-ffmpeg`.
- **Service URLs**: Fixed `DOCUMENT_PROCESSOR_URL` to point to `surya-ocr:8000` in docker-compose.
- **Worker Dependencies**: Added `surya-ocr` to `depends_on` for image workers.

## [2.1.4] - 2026-01-10

### Fixed (Hotfix)
- **WhisperX**: Complete reimplementation from official repo (v3.7.4).
  - Installed `whisperx` from PyPI (handles PyTorch 2.8 + pyannote deps correctly)
  - Simplified Dockerfile using CUDA 12.4 base image
  - Created `IMPLEMENTATION_NOTES.md` documenting all past errors and lessons learned
- **Dependencies**: Now uses official WhisperX dependency chain (PyTorch 2.8, pyannote>=3.3.2)

## [2.1.3] - 2026-01-10

### Fixed (Hotfix)
- **Universal Router**: Implemented missing background consumer loop in `router.py`. Jobs now correctly flow from `intake:*` to `extract:*`.
- **Router Config**: Simplified `PROCESSOR_QUEUES` to match worker input queues (e.g., `extract:documents` instead of `extract:documents:text`).

## [2.1.1] - 2026-01-10

### Fixed
- **Surya OCR**: Updated `server.py` for compatibility with `surya-ocr >= 0.6.0` API.
- **Qdrant**: Fixed missing API key headers in Conductor API.
- **Service Resilience**: Improved health check retry logic.

---

## [2.1.0] - 2026-01-09

### Hinzugefügt
- **Intelligence-Grade Pipeline** - Priority Scoring, Dual-Path Processing (Fast/Deep)
- **Tiered Workers** - 4 spezialisierte Worker-Typen (documents, audio, images, video)
- **Audit Trail Schema** - Chain of Custody Tracking in PostgreSQL (`scripts/schema_audit_trail.sql`)
- **Dead Letter Queue** - Automatische Fehlerbehandlung mit DLQ

### Geändert
- **CUDA Image Fix** - `nvidia/cuda:12.1-cudnn8` → `nvidia/cuda:12.1.1-cudnn8` (3 Dockerfiles)
- **MEILI_MASTER_KEY** - Muss nun mindestens 16 Zeichen haben
- **docker-compose.yml** - Neues Profil `--profile intelligence` für Worker-Pool
- **README.md** - Korrigierte Installation (Pfad, Profile, Key-Hinweis)

### Dokumentation
- DOCKER_ARCHITECTURE.md aktualisiert (16+ Container)
- .env.example mit klaren Hinweisen für sichere Keys
- PROJECT_STATUS.md aktualisiert

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
- **Hybrid Search** (BM25 + Vektor) via Meilisearch + Qdrant

### Dokumentation
- ADR-007: File Processing Quality
- ADR-008: Hybrid Search Strategy

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
  - Qdrant, Meilisearch, Tika, Ollama
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
