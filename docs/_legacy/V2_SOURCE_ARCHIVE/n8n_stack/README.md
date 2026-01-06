# Conductor N8N Stack

Hybride AI-Orchestrierung basierend auf n8n, Nextcloud, Qdrant und Ollama.

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐│
│  │ Traefik │  │   n8n   │  │ Qdrant  │  │   Nextcloud    ││
│  │  :80    │  │  :5678  │  │  :6333  │  │     :8081      ││
│  └────┬────┘  └────┬────┘  └────┬────┘  └───────┬─────────┘│
│       └────────────┴────────────┴───────────────┘          │
│                         │                                   │
│              ┌──────────┴──────────┐                       │
│              │  Redis   │ Postgres │                       │
│              │  :6379   │  :5432   │                       │
│              └──────────────────────┘                       │
└───────────────────────────┬─────────────────────────────────┘
                            │ Tailscale / LAN
┌───────────────────────────┴─────────────────────────────────┐
│                    Laptop (RTX 5090)                        │
│            ┌──────────┐  ┌───────────────┐                 │
│            │  Ollama  │  │  Whisper API  │                 │
│            │  :11434  │  │    :9000      │                 │
│            └──────────┘  └───────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Pi Setup (Orchestration + Storage)

```bash
# Clone auf Pi
scp -r n8n_stack docker@conductor-pi:~/conductor/

# SSH auf Pi
ssh conductor-pi

# Environment konfigurieren
cd ~/conductor/n8n_stack
cp .env.example .env
nano .env  # Passwörter setzen!

# Starten
docker compose up -d
```

### 2. GPU Worker Setup (Laptop)

```bash
# Voraussetzungen
# - Docker mit NVIDIA Container Toolkit
# - NVIDIA Treiber + CUDA

# Starten
docker compose -f docker-compose.gpu.yml up -d

# Ollama Models laden
docker exec conductor-ollama ollama pull llama3.2
docker exec conductor-ollama ollama pull mistral
```

## URLs

| Service | URL |
|---------|-----|
| n8n Workflow Editor | http://192.168.1.254:5678 |
| Nextcloud | http://192.168.1.254:8081 |
| Qdrant Dashboard | http://192.168.1.254:6333/dashboard |
| Traefik Dashboard | http://192.168.1.254:8080 |
| Ollama API | http://LAPTOP_IP:11434 |
| Whisper API | http://LAPTOP_IP:9000 |

## n8n Erste Schritte

1. **n8n öffnen:** http://192.168.1.254:5678
2. **Account erstellen** (erster Start)
3. **Credentials anlegen:**
   - Nextcloud API (Token aus Nextcloud → Settings → Security)
   - Ollama (Basis-URL: http://LAPTOP_IP:11434)
   - Qdrant (URL: http://qdrant:6333)

## Beispiel-Workflows

### Audio-Transkription

```
[Nextcloud Trigger] → [HTTP: Download] → [HTTP: Whisper API] → 
[Set Node: Format] → [Nextcloud: Upload .transcript.md]
```

### RAG Ingestion

```
[Schedule: 03:00] → [Nextcloud: List Files] → [Filter: .md/.txt] →
[Loop] → [Read Content] → [Text Splitter] → [Qdrant: Upsert]
```

## Ressourcen

- RAM-Verbrauch Pi: ~3.5GB (alle Services)
- Disk für n8n Data: ~500MB
- Disk für Qdrant: ~2GB pro 100K Dokumente
- Disk für Nextcloud: variabel

## Backup

```bash
# Docker Volumes sichern
docker run --rm -v n8n_data:/data -v $(pwd):/backup alpine tar czf /backup/n8n_backup.tar.gz /data
docker run --rm -v qdrant_data:/data -v $(pwd):/backup alpine tar czf /backup/qdrant_backup.tar.gz /data
```
