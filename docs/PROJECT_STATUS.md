# Conductor Project - Status & Agent Handoff

> Dieses Dokument dient als Übergabedokumentation für KI-Agenten

---

## Projektstatus: 95% Komplett

### Abgeschlossene Komponenten

| Komponente | Status | Beschreibung |
|------------|--------|--------------|
| Docker Infrastructure | ✅ 100% | 20+ Services in docker-compose.yml |
| Document Processing Pipeline | ✅ 100% | Universal Router → Orchestrator → Workers |
| Neural Search API | ✅ 100% | RAG + LLM Synthese mit SSE Streaming |
| Mission Control UI | ✅ 100% | React Frontend mit 4 Tabs |
| Startup Scripts | ✅ 100% | PowerShell + Bash Scripts |
| Dokumentation | ✅ 100% | Technische Docs erstellt |

### Offene Punkte (5%)

| Punkt | Priorität | Aufwand |
|-------|-----------|---------|
| Docker Build Test | Medium | 30 min |
| Meilisearch Initial Index | Medium | 15 min |
| Ollama Model Pull | Low | 10 min |
| End-to-End Test | Low | 1h |

---

## Wichtige Dateipfade

### Frontend (React)
```
mission_control_v2/
├── src/
│   ├── App.tsx                          # Haupt-App mit Tab-Navigation
│   ├── components/
│   │   ├── neural-search/               # Neural Search UI
│   │   │   ├── NeuralSearchPage.tsx     # Hauptseite
│   │   │   ├── SearchProgress.tsx       # 4-Step Animation
│   │   │   ├── StreamingResponse.tsx    # Antwort + Citations
│   │   │   ├── SourceCard.tsx           # Multi-Modal Preview
│   │   │   ├── FollowUpSuggestions.tsx  # Related Questions
│   │   │   └── PipelineStatusHeader.tsx # Status Bar
│   │   └── ui/                          # shadcn/ui Components
│   └── types/
│       └── neural-search.ts             # TypeScript Interfaces
└── package.json
```

### Backend (Python)
```
docker/
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
├── document-processor/
│   ├── Dockerfile                       # GPU Version
│   ├── Dockerfile.cpu                   # CPU Version
│   └── main.py                          # Processing (8005)
└── mission-control/
    ├── Dockerfile                       # Multi-Stage Build
    └── nginx.conf                       # Reverse Proxy
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

| Service | Port | Beschreibung |
|---------|------|--------------|
| Mission Control UI | 3000 | React Frontend |
| Conductor API | 8010 | Legacy API |
| Neural Search API | 8040 | RAG + LLM |
| Orchestrator | 8020 | Job Management |
| Universal Router | 8030 | File Routing |
| Document Processor | 8005 | GPU Processing |
| Meilisearch | 7700 | Search Index |
| Redis | 6379 | Queue/Cache |
| Ollama | 11434 | LLM |
| Qdrant | 6333 | Vector Store |
| Tika | 9998 | Text Extraction |
| WhisperX | 9000 | Audio Transcription |

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
curl -X POST http://localhost:3000/api/neural-search \
  -H "Content-Type: application/json" \
  -d '{"query": "Was weiß ich über meinen Vertrag?", "limit": 8}'
```

### Pipeline Status (GET /api/pipeline/status)
```bash
curl http://localhost:3000/api/pipeline/status
```

### Streaming Search (POST /api/neural-search/stream)
```bash
curl -N http://localhost:3000/api/neural-search/stream \
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
│    UI       │◀───│   Neural    │◀───│ Meilisearch │◀───│  Document   │
│  Search     │    │  Search API │    │   Index     │    │  Processor  │
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

### 2. Meilisearch leer
**Problem:** "Keine Ergebnisse" bei erster Nutzung
**Lösung:** Dokumente indexieren via `/api/index/documents`

### 3. GPU nicht erkannt
**Problem:** Document Processor startet im CPU-Modus
**Lösung:** NVIDIA Container Toolkit installieren

---

## Nächste Schritte für Agenten

1. **Docker Build testen:**
   ```bash
   docker compose build mission-control neural-search-api
   ```

2. **Services starten:**
   ```bash
   docker compose up -d
   ```

3. **Health Check:**
   ```bash
   curl http://localhost:8040/health
   curl http://localhost:3000/health
   ```

4. **Meilisearch Index erstellen:**
   ```bash
   curl -X POST http://localhost:7700/indexes \
     -H "Content-Type: application/json" \
     -d '{"uid": "documents"}'
   ```

5. **Ollama Model laden:**
   ```bash
   docker exec conductor-ollama ollama pull llama3.2
   ```

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

*Letzte Aktualisierung: 2025-01-15*
*Erstellt von: Claude Opus 4.5*
