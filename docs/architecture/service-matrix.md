# Service Matrix

> Referenzmatrix für Architekturdiagramm ↔ docker-compose ↔ Repo-Ordner.
> Stand: 2026-01-11

| Service | Repo-Ordner | Compose Service | Ports (Host → Container) | Profiles | Volumes/Mounts | Healthcheck |
| --- | --- | --- | --- | --- | --- | --- |
| Neural Search (Perplexica) | `ui/perplexica/` | `perplexica` | `3100 → ${PERPLEXICA_PORT:-3000}`, `8180 → 8080` | default | `perplexica_data:/home/perplexica/data` | `http://localhost:${PERPLEXICA_PORT:-3000}` |
| Neural Search API | `infra/docker/neural-search-api/` | `neural-search-api` | `8040 → 8040` | default | - | `http://localhost:8040/health` |
| Conductor API | `infra/docker/conductor-api/` | `conductor-api` | `8010 → 8000` | default | `conductor_api_data:/data` | `http://localhost:8000/health` |
| Orchestrator | `infra/docker/orchestrator/` | `orchestrator` | `8020 → 8020` | default | `orchestrator_data:/data` | `http://localhost:8020/health` |
| Universal Router | `infra/docker/universal-router/` | `universal-router` | `8030 → 8030` | default | - | `http://localhost:8030/health` |
| Document Processor (GPU) | `infra/docker/document-processor/` | `document-processor` | `8005 → 8000` | `gpu` | `huggingface_cache:/root/.cache/huggingface` | `http://localhost:8005/health` |
| Document Processor (CPU) | `infra/docker/document-processor/` | `document-processor-cpu` | `8006 → 8000` | `cpu` | `huggingface_cache:/root/.cache/huggingface` | `http://localhost:8006/health` |
| Qdrant | - | `qdrant` | `6335 → 6333`, `6336 → 6334` | default | `qdrant_data:/qdrant/storage` | `http://localhost:6335/collections` |
| Redis | - | `redis` | `6379 → 6379` | default | `redis_data:/data` | `redis://localhost:6379` |
| Ollama | - | `ollama` | `11435 → 11434` | default | `ollama_data:/root/.ollama` | `http://localhost:11435/api/tags` |
| Tika | - | `tika` | `9998 → 9998` | default | - | `http://localhost:9998/tika` |

**Hinweise**
- Profile `gpu`/`cpu` für Document Processor sind optional und hängen von deiner Hardware ab.
- Healthchecks sind die im Compose hinterlegten oder üblichen Readiness-URLs.
