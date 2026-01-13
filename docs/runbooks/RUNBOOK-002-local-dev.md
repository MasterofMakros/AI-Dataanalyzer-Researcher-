# Runbook: Local Development

> Ziel: Lokale Entwicklungsumgebung schnell aufsetzen und validieren.

## Voraussetzungen
- Docker + Docker Compose
- Git
- (Optional) NVIDIA GPU für das `gpu`-Profil

## Setup
```bash
cp .env.example .env
docker compose up -d
```

## Optional: GPU-Profile
```bash
docker compose --profile gpu up -d
```

## Validation
```bash
./scripts/validate.sh
```

## Healthchecks (Quick)
- http://localhost:3100 (Perplexica UI)
- http://localhost:8010/health (Conductor API)
- http://localhost:8040/health (Neural Search API)
