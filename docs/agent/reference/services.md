# Service Registry & Ports

Source of truth for service endpoints. Updated from `docker-compose.yml` and `README.md`.

## Core Services

| Service Name | Docker Service | Internal Port | Host Port | Health URL |
| :--- | :--- | :--- | :--- | :--- |
| **Mission Control** | `mission-control` | 80 | **3000** | `http://localhost:3000/health` (via wget) |
| **Perplexica** | `perplexica` | 3000 | **3100** | `http://localhost:3100` |
| **Conductor API** | `conductor-api` | 8000 | **8010** | `http://localhost:8010/health` |
| **Neural API** | `neural-search-api`| 8040 | **8040** | `http://localhost:8040/health` |
| **Orchestrator** | `orchestrator` | 8020 | **8020** | `http://localhost:8020/health` |
| **Universal Router**| `universal-router`| 8030 | **8030** | `http://localhost:8030/health` |

## Infrastructure

| Service Name | Host Port | Notes |
| :--- | :--- | :--- |
| **Qdrant** | 6335 | Vector DB |
| **Ollama** | 11435 | LLM Inference |
| **Redis** | - | Internal only (Conductor/N8N) |
| **Postgres** | - | Internal only (N8N) |

## Dependencies
- **Frontend:** React, Next.js (Perplexica)
- **Backend:** Python (FastAPI)
- **Database:** Qdrant (Vector), Postgres (N8N relational), Redis (Queue)
