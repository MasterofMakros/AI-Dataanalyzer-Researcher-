# Service Matrix

> Referenzmatrix für Architekturdiagramm ↔ docker-compose ↔ Repo-Ordner.
> Stand: 2026-01-11

| Service | Repo-Ordner | Compose-Datei | Compose Service | Ports (Host → Container) | Profiles | Volumes/Mounts | Healthcheck | Hinweise |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Traefik | - | `docker-compose.yml` | `traefik` | `8888 → 8888` | default | `/var/run/docker.sock:/var/run/docker.sock:ro` | - | Dashboard nur intern (kein externes Expose) |
| PostgreSQL | - | `docker-compose.yml` | `postgres` | - | default | `postgres_data:/var/lib/postgresql/data` | `pg_isready` | kein Host-Port (nur intern) |
| Redis | - | `docker-compose.yml` | `redis` | - | default | `redis_data:/data` | `redis-cli ping` | kein Host-Port (nur intern) |
| Redis | - | `docker-compose.intelligence.yml` | `redis` | `6379 → 6379` | default | `redis_data:/data` | `redis-cli ping` | extern für Ops/Debugging |
| n8n | - | `docker-compose.yml` | `n8n` | `5680 → 5678` | default | `n8n_data:/home/node/.n8n` | - | Workflow Engine |
| Qdrant | - | `docker-compose.yml` | `qdrant` | `6335 → 6333`, `6336 → 6334` | default | `qdrant_data:/qdrant/storage` | - | 6334 = gRPC |
| Qdrant | - | `docker-compose.intelligence.yml` | `qdrant` | `6333 → 6333` | default | `qdrant_data:/qdrant/storage` | - | nur REST offen |
| Tika | - | `docker-compose.yml` | `tika` | `9998 → 9998` | default | - | - | Text Extraction |
| Ollama | - | `docker-compose.yml` | `ollama` | `11435 → 11434` | default | `ollama_data:/root/.ollama` | - | LLM Backend |
| Ollama | - | `docker-compose.intelligence.yml` | `ollama` | `11434 → 11434` | default | `ollama_data:/root/.ollama` | - | LLM Backend |
| Whisper (legacy) | - | `docker-compose.yml` | `whisper` | `9001 → 8000` | `legacy` | `whisper_models:/root/.cache/huggingface` | - | DEPRECATED, nur `legacy` |
| WhisperX | - | `docker-compose.yml` | `whisperx` | `9000 → 9000` | default | `whisper_models:/root/.cache/huggingface` | `http://localhost:9000/health` | Empfehlung für Audio |
| Surya OCR | - | `docker-compose.yml` | `surya-ocr` | `9999 → 8000` | default | `huggingface_cache:/root/.cache/huggingface` | `http://localhost:8000/health` | Empfehlung für OCR |
| Scientific Parser | `infra/docker/scientific-parser/` | `docker-compose.yml` | `scientific-parser` | `8050 → 8050` | default | - | `http://localhost:8050/health` | Tabular/Text Extraction |
| Metadata Extractor | `infra/docker/metadata-extractor/` | `docker-compose.yml` | `metadata-extractor` | `8015 → 8000` | default | - | `http://localhost:8000/health` | ExifTool Wrapper |
| Metadata Extractor | `infra/docker/metadata-extractor/` | `docker-compose.intelligence.yml` | `metadata-extractor` | `8015 → 8000` | default | - | `http://localhost:8015/health` | Host-Port 8015 (special-parser nutzt 8016) |
| Document Processor (GPU) | `infra/docker/document-processor/` | `docker-compose.yml` | `document-processor` | `8005 → 8000` | `gpu` | `huggingface_cache:/root/.cache/huggingface`, `lancedb_data:/data/lancedb` | `http://localhost:8000/health` | ersetzt neural-worker |
| Document Processor (CPU) | `infra/docker/document-processor/` | `docker-compose.yml` | `document-processor-cpu` | `8005 → 8000` | `cpu` | `huggingface_cache:/root/.cache/huggingface`, `lancedb_data:/data/lancedb` | `http://localhost:8000/health` | gleicher Host-Port wie GPU |
| Neural Worker (legacy) | `infra/docker/neural-worker/` | `docker-compose.yml` | `neural-worker` | `8006 → 8000` | `legacy` | `huggingface_cache:/root/.cache/huggingface`, `lancedb_data:/lancedb_storage` | `http://localhost:8000/health` | DEPRECATED |
| Universal Router | `infra/docker/universal-router/` | `docker-compose.yml` | `universal-router` | `8030 → 8030` | default | - | `http://localhost:8030/health` | Magic Byte Routing |
| Universal Router | `infra/docker/universal-router/` | `docker-compose.intelligence.yml` | `universal-router` | `8030 → 8030` | default | - | `http://localhost:8030/health` | Magic Byte Routing |
| Orchestrator | `infra/docker/orchestrator/` | `docker-compose.yml` | `orchestrator` | `8020 → 8020` | default | - | `http://localhost:8020/health` | Queue Management |
| Orchestrator | `infra/docker/orchestrator/` | `docker-compose.intelligence.yml` | `orchestrator` | `8020 → 8020` | default | - | `http://localhost:8020/health` | Queue Management |
| Conductor API | `infra/docker/conductor-api/` | `docker-compose.yml` | `conductor-api` | `8010 → 8000` | default | `conductor_api_data:/data` | `http://localhost:8000/health` | zentrale API |
| Conductor API | `infra/docker/conductor-api/` | `docker-compose.intelligence.yml` | `conductor-api` | `8010 → 8000` | default | `conductor_api_data:/data` | `http://localhost:8000/health` | zentrale API |
| Neural Search (Perplexica) | `ui/perplexica/` | `docker-compose.yml` | `perplexica` | `3100 → ${PERPLEXICA_PORT:-3000}`, `8180 → 8080` | default | `perplexica_data:/home/perplexica/data` | `http://localhost:${PERPLEXICA_PORT:-3000}` | UI + SearxNG |
| Neural Search API | `infra/docker/neural-search-api/` | `docker-compose.yml` | `neural-search-api` | `8040 → 8040` | default | - | `http://localhost:8040/health` | RAG + LLM |
| Nextcloud | - | `docker-compose.yml` | `nextcloud` | `8081 → 80` | default | `nextcloud_data:/var/www/html` | - | Filesync |
| Nextcloud DB | - | `docker-compose.yml` | `nextcloud-db` | - | default | `mariadb_data:/var/lib/mysql` | - | kein Host-Port |
| Special Parser | `infra/docker/special-parser/` | `docker-compose.intelligence.yml` | `special-parser` | `8016 → 8015` | default | - | `http://localhost:8016/health` | Overlay-only Host-Port 8016 (kein Konflikt) |

**Hinweise**
- Profile `gpu`/`cpu` für Document Processor sind optional und hängen von deiner Hardware ab.
- Services ohne Host-Port sind nur im internen Docker-Netz erreichbar.


**Check-Script**
- `scripts/check_service_ports.py` vergleicht Compose-Ports mit dieser Tabelle.
