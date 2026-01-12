# Docker Architecture

> Neural Vault Docker-basierte Architektur
> Stand: 09.01.2026

---

## Service-Übersicht

Neural Vault besteht aus **16+ Docker-Containern**, die über ein internes Netzwerk kommunizieren:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONDUCTOR DOCKER STACK                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Traefik   │  │   Postgres  │  │    Redis    │  │  Nextcloud  │        │
│  │   :8888     │  │   :5432     │  │   :6379     │  │   :8081     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │     n8n     │  │   Qdrant    │  │ Meilisearch │  │   Ollama    │        │
│  │   :5680     │  │   :6335     │  │   :7700     │  │  :11435     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    BINARY PROCESSING LAYER                       │        │
│  ├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤        │
│  │   Whisper   │   FFmpeg    │  Tesseract  │    Tika     │  7-Zip  │        │
│  │   :9001     │   (exec)    │   (exec)    │   :9998     │  (exec) │        │
│  └─────────────┴─────────────┴─────────────┴─────────────┴─────────┘        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                     AI PROCESSING LAYER                          │        │
│  ├─────────────────────────────────────────────────────────────────┤        │
│  │                   Document Processor                            │        │
│  │                        :8005                                    │        │
│  │              (Docling + GLiNER + Surya)                         │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    CONDUCTOR API (NEU)                           │        │
│  │                         :8010                                    │        │
│  │  - Volltextsuche (Meilisearch)                                   │        │
│  │  - Pattern-of-Life Analyse                                       │        │
│  │  - Context Headers für RAG                                       │        │
│  │  - Feedback Tracking                                             │        │
│  │  - Tika HTML→Markdown                                            │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Container-Details

| Service | Image | External Port | Internal Port | Memory | Funktion |
|:--------|:------|:--------------|:--------------|:-------|:---------|
| **conductor-api** | conductor-api:latest | 8010 | 8000 | 512M | Zentrale API |
| **mission-control** | mission-control:latest | 3000 | 80 | 128M | Mission Control UI |
| **neural-search** | neural-search-api:latest | 8040 | 8040 | 512M | RAG & LLM API |
| traefik | traefik:v3.2 | 8888 | 8888 | 128M | Reverse Proxy |
| postgres | postgres:16-alpine | - | 5432 | 256M | n8n Database |
| redis | redis:7.4-alpine | 6379 | 6379 | 128M | Cache + State |
| n8n | n8nio/n8n:latest | 5680 | 5678 | 768M | Workflow Engine |
| qdrant | qdrant/qdrant:latest | 6335 | 6333 | 1G | Vector DB (GRPC: 6336 -> 6334) |
| meilisearch | getmeili/meilisearch:latest | 7700 | 7700 | 512M | Fulltext Search |
| ollama | ollama/ollama:latest | 11435 | 11434 | 8G | Local LLM |
| tika | apache/tika:latest | 9998 | 9998 | 1G | Document Parser |
| whisperx | conductor-whisperx:latest | 9000 | 9000 | 8G | Audio Transkription |
| ffmpeg-api | jrottenberg/ffmpeg:7-ubuntu | - | - | 1G | Video Metadaten |
| surya-ocr | conductor-surya-ocr:latest | 9999 | 8000 | 6G | OCR (GPU) |
| document-processor | conductor-document-processor:latest | 8005 | 8000 | 8G | Docling + GLiNER |

**Gesamt-Memory:** ~23 GB (mit GPU-Offload auf Ollama weniger)

---

## Conductor API Endpoints

Die neue **conductor-api** fasst alle Funktionen in einer REST-API zusammen:

### Suche

```bash
# Volltextsuche
curl -X POST http://localhost:8010/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Rechnung 2024", "limit": 20}'

# Pattern-of-Life: Dateien von Sonntagen
curl "http://localhost:8010/search/pattern-of-life?weekday=6&limit=50"

# Pattern-of-Life: Nachts (22-06 Uhr) erstellt
curl "http://localhost:8010/search/pattern-of-life?hour_min=22&hour_max=6"
```

### Extraktion

```bash
# Dokument extrahieren (HTML→Markdown)
curl -X POST http://localhost:8010/extract \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/mnt/data/dokument.pdf", "prefer_markdown": true}'

# Mit Context Header für RAG
curl -X POST http://localhost:8010/extract/with-context \
  -d "file_path=/mnt/data/rechnung.pdf&category=Finanzen&confidence=0.92"
```

### Feedback

```bash
# Korrektur loggen
curl -X POST http://localhost:8010/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "file_hash": "abc123",
    "filename": "Rechnung.pdf",
    "predicted_category": "Privat",
    "actual_category": "Geschäftlich"
  }'

# Statistiken abrufen
curl http://localhost:8010/feedback/stats

# Confusion Matrix
curl http://localhost:8010/feedback/confusion-matrix
```

### Index-Management

```bash
# Index konfigurieren (einmalig)
curl -X POST http://localhost:8010/index/setup

# Index-Statistiken
curl http://localhost:8010/index/stats

# Dokumente indexieren
curl -X POST http://localhost:8010/index/documents \
  -H "Content-Type: application/json" \
  -d '{"documents": [{"id": "1", "original_filename": "test.pdf", ...}]}'
```

### Health Check

```bash
curl http://localhost:8010/health
# {
#   "status": "healthy",
#   "services": {
#     "meilisearch": true,
#     "tika": true,
#     "redis": true,
#     "qdrant": true,
#     "ollama": true
#   },
#   "timestamp": "2025-12-28T15:30:00"
# }
```

---

## Schnellstart

### Windows

```batch
cd F:\conductor

REM Alle Services starten
scripts\docker_start.bat

REM Nur API + Dependencies
scripts\docker_start.bat api

REM Logs anzeigen
scripts\docker_start.bat logs

REM Index konfigurieren
scripts\docker_start.bat setup-index

REM Stoppen
scripts\docker_start.bat stop
```

### Linux/Mac

```bash
cd /path/to/conductor

# Alle Services starten
./scripts/docker_start.sh

# Nur API + Dependencies
./scripts/docker_start.sh api

# Logs anzeigen
./scripts/docker_start.sh logs

# Index konfigurieren
./scripts/docker_start.sh setup-index

# Stoppen
./scripts/docker_start.sh stop
```

---

## Environment Variables

Alle Secrets werden über `.env` konfiguriert:

```env
# Required
POSTGRES_PASSWORD=sicheres_passwort
REDIS_PASSWORD=sicheres_passwort
MEILI_MASTER_KEY=min_16_zeichen_key
N8N_ENCRYPTION_KEY=min_32_zeichen_key
NC_DB_PASSWORD=sicheres_passwort
NC_DB_ROOT_PASSWORD=sicheres_passwort
NC_ADMIN_PASSWORD=sicheres_passwort

# Optional
QDRANT_API_KEY=
WEBHOOK_URL=http://localhost:5678/
GENERIC_TIMEZONE=Europe/Berlin
```

---

## Netzwerk-Architektur

Alle Services kommunizieren über das interne `conductor-net` Bridge-Netzwerk:

```
┌─────────────────────────────────────────────────────────────────┐
│                     conductor-net (bridge)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   conductor-api ──► meilisearch (http://meilisearch:7700)       │
│         │                                                        │
│         ├──────► tika (http://tika:9998)                        │
│         │                                                        │
│         ├──────► redis (redis://redis:6379)                     │
│         │                                                        │
│         ├──────► qdrant (http://qdrant:6333)                    │
│         │                                                        │
│         └──────► ollama (http://ollama:11434)                   │
│                                                                  │
│   n8n ──────────► conductor-api (http://conductor-api:8000)     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Volume-Mappings

| Volume | Mount | Zweck |
|:-------|:------|:------|
| `F:/` | `/mnt/data:ro` | Datenpool (Read-Only) |
| `conductor_api_data` | `/data` | Feedback DB, Cache |
| `meilisearch_data` | `/meili_data` | Suchindex |
| `qdrant_data` | `/qdrant/storage` | Vektoren |
| `ollama_data` | `/root/.ollama` | LLM-Modelle |

---

## Rebuild einzelner Services

```bash
# Conductor API neu bauen
docker compose build conductor-api
docker compose up -d conductor-api

# Parser Service neu bauen
docker compose build parser-service
docker compose up -d parser-service

# Alle Custom-Images neu bauen
docker compose build
```

---

## Troubleshooting

### Service startet nicht

```bash
# Logs prüfen
docker compose logs conductor-api

# Container-Status
docker compose ps

# In Container einloggen
docker exec -it conductor-api bash
```

### Meilisearch Index Reset

```bash
curl -X POST "http://localhost:8010/index/setup?reset=true"
```

### Memory-Probleme

```bash
# Memory-Verbrauch prüfen
docker stats

# Einzelne Services neustarten
docker compose restart conductor-api
```

---

*Dokumentation aktualisiert: 28.12.2025*
