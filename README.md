# Conductor

> **Ein lokales, privates "Internes Google" für 10TB+ Lebensdaten.**

[![Status](https://img.shields.io/badge/Status-Active%20Development-green)]()
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)]()

## Was ist das?

Conductor ist ein **vollständig lokales** System zur automatischen Organisation, Deduplizierung und semantischen Suche über große Datenmengen (Dokumente, Fotos, Videos, E-Mails). Es nutzt KI-Modelle (Ollama, WhisperX, Surya OCR), die auf deiner eigenen Hardware laufen - keine Cloud, keine Abos, keine Daten-Leaks.

**Das Kernversprechen:** Finde jede Rechnung, jedes Foto, jede Notiz in unter 3 Sekunden.

---

## Features

- **Neural Search UI** - Perplexity-ähnliche Suchoberfläche mit KI-generierten Antworten
- **RAG Pipeline** - Retrieval-Augmented Generation mit Quellenverweisen
- **Multi-Modal Processing** - 127+ Dateiformate: PDF, Audio, Video, Bilder, E-Mails
- **Local Search** - Semantische Suche in lokalen Dokumenten mit Optimization Modes
- **Media Preview** - Video/Audio-Player mit Timecode-Navigation und Transkript-Overlay
- **Automatische Klassifizierung** - KI-basierte Dokumentenkategorisierung
- **Vektor-Suche** - Qdrant für semantische Ähnlichkeitssuche
- **Intelligence-Grade Pipeline** - Priority Queues, Dual-Path Processing, Dead Letter Queue
- **Audit Trail** - Lückenlose Chain of Custody für alle Dokumente
- **100% Lokal** - Alle Daten bleiben auf deiner Hardware

---

## 🚀 Schnellstart

### Voraussetzungen

- **Docker & Docker Compose** installiert
- **NVIDIA GPU** (empfohlen für volle Performance) oder CPU-Modus
- **Git**
- Mindestens 16GB RAM
- 10TB+ Speicher (für große Datenmengen)

### Installation

```bash
# 1. Repository klonen
git clone https://github.com/MasterofMakros/AI-Dataanalyzer-Researcher-.git
cd AI-Dataanalyzer-Researcher-

# 2. Environment konfigurieren
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux/macOS
cp .env.example .env

# .env anpassen (Pfade, API Keys)

# 3. Services starten
docker compose up -d

# Mit GPU-Profil (für OCR, Whisper)
docker compose --profile gpu up -d

# Intelligence-Grade (10 parallele Worker)
docker compose --profile intelligence up -d
```

### Validation

```bash
# Windows
./scripts/validate.ps1

# Linux/macOS
./scripts/validate.sh
```

### Überprüfung

Nach dem Start sind folgende Services verfügbar:

| Service | URL | Beschreibung |
|---------|-----|--------------|
| Neural Search (Perplexica) | http://localhost:3100 | Web UI mit Local Search |
| Conductor API | http://localhost:8010 | REST API |
| Neural Search API | http://localhost:8040 | RAG + LLM Backend |
| Qdrant | http://localhost:6335 | Vektor-Datenbank |
| Ollama | http://localhost:11435 | LLM Backend |
| Orchestrator | http://localhost:8020 | Pipeline Stats |

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                 Neural Search (Perplexica) :3100                │
│            + Local Search + Media Preview + Format Icons        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
┌─────────────────┐ ┌───────────┐ ┌──────────────┐
│ Neural Search   │ │ Conductor │ │ Orchestrator │
│ API :8040       │ │ API :8010 │ │ :8020        │
│ (RAG + LLM)     │ │           │ │              │
└────────┬────────┘ └─────┬─────┘ └──────┬───────┘
         │                │              │
    ┌────┴────┐     ┌─────┴─────┐   ┌────┴────┐
    ▼         ▼     ▼           ▼   ▼         ▼
┌───────┐ ┌──────┐ ┌────────┐ ┌──────┐ ┌──────────┐
│Qdrant │ │Ollama│ │Redis   │ │      │ │Document  │
│:6335  │ │:11435│ │:6379   │ │      │ │Processor │
└───────┘ └──────┘ └────────┘ └──────┘ └──────────┘
```

---

## Neue Features (v2.0)

### Local Search mit Optimization Modes

Die Neural Search UI unterstützt jetzt lokale Dokumentensuche mit drei Modi:

| Mode | Limit | Beschreibung |
|------|-------|--------------|
| Speed | 3 | Schnelle Antwort, minimale Quellen |
| Balanced | 8 | Ausgewogen (Standard) |
| Quality | 15 | Gründliche Recherche, maximale Quellen |

### Media Preview

- **LocalMediaPreview** - Sidebar mit Video/Audio-Thumbnails
- **MediaPlayerModal** - Vollbild-Player mit Timecode-Navigation
- **Transkript-Overlay** - Hervorgehobene Suchbegriffe im Transkript

### Format Icons

127+ Dateiformate mit passenden Icons für die Research-Visualisierung.

---

## Dokumentation

| Dokument | Beschreibung |
|----------|--------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System-Architektur |
| [PROJECT_OVERVIEW_2025.md](PROJECT_OVERVIEW_2025.md) | Projekt-Übersicht |
| [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) | Aktueller Status |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Beitragsrichtlinien |
| [SECURITY.md](SECURITY.md) | Sicherheitsrichtlinien |

### Architektur-Entscheidungen (ADRs)

Alle technischen Entscheidungen sind in `docs/ADR/` dokumentiert.

---

## Agent Commands (PIV Loop)

Using an AI Agent? Use these Slash Commands to navigate the workflow.

| Command | Phase | Action |
| :--- | :--- | :--- |
| `/core_piv_loop:prime` | **Prime** | Load context & rules (`CLAUDE.md`) |
| `/core_piv_loop:plan-feature` | **Plan** | Create implementation plan |
| `/core_piv_loop:execute` | **Execute** | Implement approved plan |
| `/validation:validate` | **Validate** | Run local validation suite |
| `/github_bug_fix:rca` | **Fix** | Start Root Cause Analysis |

For full details, see [CLAUDE.md](CLAUDE.md).

---

## Tech Stack

| Kategorie | Technologie |
|-----------|-------------|
| Frontend | React, TypeScript, Tailwind CSS, Next.js |
| Backend | FastAPI, Python 3.11 |
| Suche | Qdrant (Vektor-Suche) |
| KI/ML | Ollama, WhisperX, Surya OCR, Docling |
| Infrastruktur | Docker, nginx, Redis |

---

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

---

*Letzte Aktualisierung: 2026-01-11*
