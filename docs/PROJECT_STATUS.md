# Conductor Project - Status & Agent Handoff

> Dieses Dokument dient als Übergabedokumentation für KI-Agenten

---

## Projektstatus: Core abgeschlossen, Roadmap offen ✅

> Status-Regel: "✅ Done (Validated)" darf nur gesetzt werden, wenn ein reproduzierbarer Runtime-Run (Commands + Reports) als Evidence verlinkt ist.

## Feature Backlog (Quelle der Wahrheit)

| ID | Feature | Status | PRP-Link | Abhängigkeiten | Validierung |
|---|---|---|---|---|---|
| F-001 | Documentation Consolidation | planned | ../PRPs/2026-01-12_consolidate-docs.md | - | `scripts/validate.ps1` |
| F-002 | Fix CI/CD Pipeline | planned | ../PRPs/2026-01-12_fix-ci-pipeline.md | - | `scripts/validate.ps1` + GitHub Actions |
| F-003 | Smoke Test - Verify Context Engineering Setup | planned | ../PRPs/2026-01-12_smoke-test.md | - | `scripts/validate.ps1` |
| F-004 | E2E Format Coverage Harness (PRP-FMT-001) | Done (Validated) | ../PRPs/prp-fmt-001-e2e-format-coverage-harness.md | Docker Daemon + Base/Overlay running | Evidence: `artifacts/e2e/base/e2e_formats_report.json`; `artifacts/e2e/overlay/e2e_formats_report.json` |
| F-005 | Perplexica UI E2E Tests (PRP-UI-002) | Implemented / Pending Validation | ../PRPs/prp-ui-002-perplexica-ui-e2e-tests.md | F-004 | `npm run test:e2e`; Evidence: `.agents/plans/2026-01-15_ui-002_runtime_evidence.md` (failed; seed inbox not empty; UI testids not found) |

### Abgeschlossene Komponenten

| Komponente | Status | Beschreibung |
|------------|--------|--------------|
| Docker Infrastructure | ✅ 100% | 20+ Services in docker-compose.yml |
| Document Processing Pipeline | ✅ 100% | Universal Router → Orchestrator → Workers |
| Neural Search API | ✅ 100% | RAG + LLM Synthese mit SSE Streaming |
| Perplexica UI | ✅ 100% | Search Frontend |
| Intelligence Pipeline | ✅ 100% | Priority Scoring, Dual-Path, DLQ |
| Tiered Workers | ✅ 100% | 4 Worker-Typen (documents, audio, images, video) |
| Audit Trail | ✅ 100% | Chain of Custody in PostgreSQL |
| Startup Scripts | ✅ 100% | PowerShell + Bash Scripts |
| Dokumentation | ✅ 100% | Technische Docs aktualisiert |
| **E2E Format Test (Harness)** | ✅ Done (Validated) | Evidence: `artifacts/e2e/base/e2e_formats_report.json`; `artifacts/e2e/overlay/e2e_formats_report.json`; `.agents/plans/2026-01-14_fmt-001_runtime_evidence.md` |
| E2E Format Test (Legacy) | ✅ (historisch) | 8/8 Formate verifiziert (v2.1.6); wird durch Harness-Evidence abgelöst |

### Verifizierte Formate

| Format | Worker | Technologie | Status | Evidence |
|--------|--------|-------------|--------|----------|
| TXT, PDF, DOCX, XLSX | Documents | Tika | ✅ (Legacy) | v2.1.6 |
| MP3, WAV, M4A | Audio | WhisperX | ✅ (Legacy) | v2.1.6 |
| MP4, MKV, AVI | Video | FFmpeg+WhisperX | ✅ (Legacy) | v2.1.6 |
| JPG, PNG, TIFF | Images | Surya OCR 0.17 | ✅ (Legacy) | v2.1.6 |

---

## Wichtige Dateipfade

### Frontend (React)
```
ui/perplexica/
├── src/                                 # App source
├── public/                              # Static assets
├── next.config.mjs                      # Next.js config
└── package.json
```

### Backend (Python)
```
infra/docker/
├── neural-search-api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── neural_search_api.py             # FastAPI Service (8040)
├── conductor-api/
│   └── api_service.py                   # Legacy API (8010)
├── universal-router/
│   └── router.py                        # File Routing (8030)
├── orchestrator/
│   └── orchestrator.py                  # Job Management (8020)
└── document-processor/
    ├── Dockerfile                       # GPU Version
    ├── Dockerfile.cpu                   # CPU Version
    └── main.py                          # Processing (8005)
```

### Konfiguration
```
├── docker-compose.yml                   # Alle Services
├── .env.example                         # Environment Template
├── config/
│   └── feature_flags.py                 # Runtime Flags
└── scripts/
    ├── start_pipeline.ps1               # Windows Startup
    └── start_pipeline.sh                # Linux/Mac Startup
```

---

## Service-Ports

| Service | Host-Port | Container-Port | Beschreibung |
|---------|-----------|----------------|--------------|
| Traefik Dashboard | 8888 | 8888 | Reverse Proxy UI |
| n8n | 5680 | 5678 | Workflow Engine |
| Perplexica UI | 3100 | 3000 | Search Frontend |
| Perplexica SearxNG | 8180 | 8080 | Metasuche |
| Conductor API | 8010 | 8000 | REST API |
| Neural Search API | 8040 | 8040 | RAG + LLM |
| Universal Router | 8030 | 8030 | File Routing |
| Orchestrator | 8020 | 8020 | Job Management |
| Document Processor | 8005 | 8000 | GPU/CPU Processing |
| WhisperX | 9000 | 9000 | Audio Transcription |
| Surya OCR | 9999 | 8000 | OCR Service |
| Tika | 9998 | 9998 | Text Extraction |
| Scientific Parser | 8050 | 8050 | Table/Text Parsing |
| Metadata Extractor | 8015 | 8000 | ExifTool Wrapper |
| Special Parser (Overlay) | 8016 | 8015 | 3D/CAD/GIS/Fonts (overlay only) |
| Qdrant (REST) | 6335 | 6333 | Vector Store |
| Qdrant (gRPC) | 6336 | 6334 | gRPC Endpoint |
| Ollama | 11435 | 11434 | LLM |
| Nextcloud | 8081 | 80 | Filesync UI |

---

## Overlay & WSL Hinweise

- 3D/CAD/GIS/Fonts Processing ist nur im Intelligence-Overlay verfügbar (`docker-compose.intelligence.yml`).
- WSL-Pfade: In WSL `CONDUCTOR_TESTSUITE=/mnt/f/_TestSuite` (Windows native: `F:\_TestSuite`).

---

## Schnellstart

### Windows
```powershell
cd F:\conductor
.\scripts\start_pipeline.ps1
```

### Linux/Mac
```bash
cd /path/to/conductor
./scripts/start_pipeline.sh
```

### Minimal (nur UI + API)
```powershell
.\scripts\start_pipeline.ps1 -Minimal
```

### Mit GPU
```powershell
.\scripts\start_pipeline.ps1 -GPU
```

---

## API-Endpunkte

### Neural Search (POST /api/neural-search)
```bash
curl -X POST http://localhost:3100/api/neural-search \
  -H "Content-Type: application/json" \
  -d '{"query": "Was weiß ich über meinen Vertrag?", "limit": 8}'
```

### Pipeline Status (GET /api/pipeline/status)
```bash
curl http://localhost:3100/api/pipeline/status
```

### Streaming Search (POST /api/neural-search/stream)
```bash
curl -N http://localhost:3100/api/neural-search/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Zeige mir meine Rechnungen"}'
```

---

## Datenfluss

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Dateien   │───▶│  Universal  │───▶│ Orchestrator│───▶│   Workers   │
│  F:\Vault   │    │   Router    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                                                                ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    UI       │◀───│   Neural    │◀───│   Qdrant    │◀───│  Document   │
│  Search     │    │  Search API │    │ Vector DB  │    │  Processor  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │
       │                  ▼
       │           ┌─────────────┐
       │           │   Ollama    │
       │           │    LLM      │
       │           └─────────────┘
       │                  │
       ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Streaming Response                             │
│  "Dein Vertrag **Magenta M** läuft seit **15.03.2022** ¹..."       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Bekannte Issues

### 1. Ollama Cold Start
**Problem:** Erste Anfrage dauert 10-30s
**Lösung:** Ollama vorwärmen mit dummy request

### 2. Qdrant leer
**Problem:** "Keine Ergebnisse" bei erster Nutzung
**Lösung:** Dokumente indexieren via `/api/index/documents`

### 3. GPU nicht erkannt
**Problem:** Document Processor startet im CPU-Modus
**Lösung:** NVIDIA Container Toolkit installieren

---

## Nächste Schritte für Agenten

1. **Docker Build testen:**
   ```bash
   docker compose build perplexica neural-search-api
   ```

2. **Services starten:**
   ```bash
   docker compose up -d
   ```

3. **Health Check:**
   ```bash
   curl http://localhost:8040/health
   curl http://localhost:3100
   ```

4. **Qdrant Collections anlegen (optional):**
   ```bash
   curl -X PUT http://localhost:6335/collections/documents \
     -H "Content-Type: application/json" \
     -d '{"vectors":{"size":1024,"distance":"Cosine"}}'
   ```

5. **Ollama Model laden:**
   ```bash
   docker exec conductor-ollama ollama pull llama3.2
   ```

---

## Validation Scope (scripts/validate.*)

Die lokalen Validate-Skripte prüfen:
- Doctor check (Umgebung/Prereqs)
- Python compile check
- Backend Tests (`pytest tests/`)
- Frontend Lint (`npm run lint --if-present`)
- Frontend Build (`npm run build --if-present`)
- Docker Compose config validation
- Smoke tests (nur wenn Container laufen)

Optional:
- `--quick`/`-Quick`: Überspringt UI build/lint + Backend Tests.
- `--skip-docker`/`-SkipDocker`: Überspringt Docker config + Smoke tests.

---

## Wichtige Konventionen

### Code-Style
- TypeScript: Functional Components mit Hooks
- Python: FastAPI mit Pydantic Models
- Keine Emojis in Code-Dateien
- Deutsche Kommentare in Docs, englische in Code

### Git
- Commits mit `Co-Authored-By: Claude`
- Branch-Namen: `feature/`, `fix/`, `docs/`

### Docker
- Multi-Stage Builds für Frontend
- Health Checks für alle Services
- Memory Limits definiert

---

## Kontextgrenzen für Agenten

### Was NICHT ändern:
- `docker-compose.yml` Grundstruktur
- Port-Zuweisungen (außer Konflikte)
- Bestehende API-Verträge

### Was geändert werden kann:
- UI-Komponenten
- API-Erweiterungen (neue Endpoints)
- Dokumentation
- Tests

---

*Letzte Aktualisierung: 2026-01-14*
*Maintainer: Human + AI Agents (Codex/CLI)*
*Evidence Logs: .agents/plans/*
