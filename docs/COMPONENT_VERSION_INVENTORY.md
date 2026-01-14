# Komponenten- und Versionsinventar

Diese Datei listet alle Komponenten, die Features im Stack bereitstellen, sowie die
aktuell verwendeten Versions-Tags/Versionsquellen. **Floating Tags** (z. B. `latest`)
werden explizit so markiert, da sie bei Updates unkontrolliert springen können.

## A) Laufzeit-Services (docker-compose.yml)

| Service | Image/Build | Version/Tag | Quelle |
| --- | --- | --- | --- |
| traefik | `traefik` | `v3.2` | `docker-compose.yml` |
| postgres | `postgres` | `16-alpine` | `docker-compose.yml` |
| redis | `redis` | `7.4-alpine` | `docker-compose.yml` |
| n8n | `n8nio/n8n` | `latest` (floating) | `docker-compose.yml` |
| qdrant | `qdrant/qdrant` | `latest` (floating) | `docker-compose.yml` |
| tika | `apache/tika` | `${TIKA_TAG:-3.2.3.0}` | `docker-compose.yml`, `.env.example` |
| ollama | `ollama/ollama` | `latest` (floating) | `docker-compose.yml` |
| whisper (legacy) | `fedirz/faster-whisper-server` | `${FASTER_WHISPER_CUDA_TAG:-latest-cuda}` | `docker-compose.yml`, `.env.example` |
| whisperx | build: `infra/docker/whisperx-api` | `WHISPERX_VERSION` (PyPI pin) | `docker-compose.yml`, `.env.example`, `Dockerfile` |
| ffmpeg-api | `jrottenberg/ffmpeg` | `7-ubuntu` | `docker-compose.yml` |
| tesseract-ocr (legacy) | `jitesoft/tesseract-ocr` | `latest` (floating) | `docker-compose.yml` |
| surya-ocr | build: `infra/docker/surya-ocr` | base image `nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04` | `docker-compose.yml`, Dockerfile |
| scientific-parser | build: `infra/docker/scientific-parser` | base image `python:3.11-slim-bookworm` | `docker-compose.yml`, Dockerfile |
| sevenzip | `crazymax/7zip` | `latest` (floating) | `docker-compose.yml` |
| metadata-extractor | build: `infra/docker/metadata-extractor` | base image `python:3.11-slim` | `docker-compose.yml`, Dockerfile |
| document-processor (GPU) | build: `infra/docker/document-processor` | base image `nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04` | `docker-compose.yml`, Dockerfile |
| document-processor (CPU) | build: `infra/docker/document-processor` | base image `python:3.11-slim-bookworm` | `docker-compose.yml`, Dockerfile.cpu |
| neural-worker (legacy) | build: `infra/docker/neural-worker` | base image `python:3.11-slim-bookworm` | `docker-compose.yml`, Dockerfile |
| universal-router | build: `infra/docker/universal-router` | base image `python:3.11-slim` | `docker-compose.yml`, Dockerfile |
| orchestrator | build: `infra/docker/orchestrator` | base image `python:3.11-slim` | `docker-compose.yml`, Dockerfile |
| extraction-worker(s) | build: `infra/docker/workers` | base image `python:3.11-slim` | `docker-compose.yml`, Dockerfile |
| conductor-api | build: `infra/docker/conductor-api` | base image `python:3.11-slim` | `docker-compose.yml`, Dockerfile |
| perplexica (UI) | build: `ui/perplexica` | app version `1.12.1`; base image `node:24.5.0-slim` | `docker-compose.yml`, `package.json`, Dockerfile |
| neural-search-api | build: `infra/docker/neural-search-api` | base image `python:3.11-slim-bookworm` | `docker-compose.yml`, Dockerfile |
| nextcloud | `nextcloud` | `30-apache` | `docker-compose.yml` |
| nextcloud-db | `mariadb` | `11` | `docker-compose.yml` |

## B) Intelligence-Stack (docker-compose.intelligence.yml)

| Service | Image/Build | Version/Tag | Quelle |
| --- | --- | --- | --- |
| redis | `redis` | `7.4-alpine` | `docker-compose.intelligence.yml` |
| universal-router | build: `infra/docker/universal-router` | base image `python:3.11-slim` | `docker-compose.intelligence.yml`, Dockerfile |
| orchestrator | build: `infra/docker/orchestrator` | base image `python:3.11-slim` | `docker-compose.intelligence.yml`, Dockerfile |
| special-parser | build: `infra/docker/special-parser` | base image `python:3.11-slim` | `docker-compose.intelligence.yml`, Dockerfile |
| worker-* | build: `infra/docker/workers` | base image `python:3.11-slim` | `docker-compose.intelligence.yml`, Dockerfile |
| tika | `apache/tika` | `${TIKA_TAG:-3.2.3.0}` | `docker-compose.intelligence.yml`, `.env.example` |
| whisper-fast | `fedirz/faster-whisper-server` | `${FASTER_WHISPER_TAG:-latest}` | `docker-compose.intelligence.yml`, `.env.example` |
| whisper-accurate | `fedirz/faster-whisper-server` | `${FASTER_WHISPER_CUDA_TAG:-latest-cuda}` | `docker-compose.intelligence.yml`, `.env.example` |
| ffmpeg | `jrottenberg/ffmpeg` | `7-ubuntu` | `docker-compose.intelligence.yml` |

## C) UI-spezifisch (Perplexica)

- App-Version: **1.12.1** (lokal gepflegt; keine direkte Upstream-Updates, um Modifikationen zu schützen).
- Build-Image: **node:24.5.0-slim** (Dockerfile).

## D) Bereiche mit ähnlichen Update-Risiken

Diese Stellen können bei Updates „springen“, weil Versionen **nicht** fest gepinnt sind:

1. **Floating Docker-Tags (`latest`)**
   - `n8nio/n8n:latest`, `qdrant/qdrant:latest`, `ollama/ollama:latest`,
     `jitesoft/tesseract-ocr:latest`, `crazymax/7zip:latest`.
2. **Python-Abhängigkeiten mit `>=` in `infra/docker/document-processor/requirements.txt`**
   - z. B. `docling>=2.0.0`, `surya-ocr>=0.6.0`, `gliner>=0.2.0`, `torch>=2.0.0`.
3. **Node/JS-Abhängigkeiten mit `^` im Perplexica UI (`ui/perplexica/package.json`)**
   - semver-float kann beim `npm/yarn install` zu Versionssprüngen führen.

## E) Empfohlene Pflege-Strategie (kurz)

- **Docker-Images pinnen**: statt `latest` feste Tags setzen (z. B. `qdrant/qdrant:1.13.x`).
- **Python-Dependencies einfrieren**: `>=` → konkrete Pins, ggf. `pip-compile`.
- **UI-Updates**: eigenes Fork + Patch-Workflow (kein Direkt-Reset auf Upstream).
