# Intelligence-Grade Processing Architecture

> Wie Geheimdienste Dokumenten-Processing strukturieren würden
> Analyse basierend auf öffentlichen Informationen über NSA XKEYSCORE, Palantir Gotham, GCHQ TEMPORA

---

## Fundamentale Unterschiede

| Aspekt | Consumer-Ansatz (aktuell) | Intelligence-Grade |
|:-------|:--------------------------|:-------------------|
| **Architektur** | Monolithische Services | Micro-Pipeline Assembly Line |
| **Skalierung** | Vertikal (mehr RAM) | Horizontal (mehr Worker) |
| **Priorisierung** | FIFO (First In, First Out) | Priority Queues + Triage |
| **Fehlerbehandlung** | Retry & Skip | Dead Letter Queue + Manual Review |
| **Logging** | Optional | Chain of Custody (unveränderlich) |
| **Processing** | Synchron | Asynchron mit Checkpoints |

---

## Das "Assembly Line" Modell

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTELLIGENCE PROCESSING PIPELINE                      │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
     │  INGEST  │ ───► │  TRIAGE  │ ───► │ EXTRACT  │ ───► │  ENRICH  │
     │  LAYER   │      │  LAYER   │      │  LAYER   │      │  LAYER   │
     └──────────┘      └──────────┘      └──────────┘      └──────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
     ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
     │ Hash +   │      │ Priority │      │ Content  │      │ Entity   │
     │ Metadata │      │ Score    │      │ Text     │      │ Linking  │
     └──────────┘      └──────────┘      └──────────┘      └──────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
     ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
     │ CLASSIFY │ ───► │  INDEX   │ ───► │  ALERT   │ ───► │ ARCHIVE  │
     │  LAYER   │      │  LAYER   │      │  LAYER   │      │  LAYER   │
     └──────────┘      └──────────┘      └──────────┘      └──────────┘
```

---

## Docker-Service-Matrix nach Dateityp

### Tier 1: Intake Workers (Parallelisierbar, Stateless)

```yaml
# Jeder Dateityp bekommt dedizierte Worker-Pools
services:

  # ═══════════════════════════════════════════════════════════════════════════
  # DOCUMENT INTAKE (PDF, DOCX, XLSX, etc.)
  # ═══════════════════════════════════════════════════════════════════════════

  intake-documents:
    image: conductor-intake:documents
    deploy:
      replicas: 4  # Horizontal skalieren
      resources:
        limits:
          memory: 512M
    environment:
      - WORKER_TYPE=documents
      - QUEUE=intake:documents
      - OUTPUT_QUEUE=extract:documents

  # ═══════════════════════════════════════════════════════════════════════════
  # MEDIA INTAKE (Video, Audio, Bilder)
  # ═══════════════════════════════════════════════════════════════════════════

  intake-media:
    image: conductor-intake:media
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
    environment:
      - WORKER_TYPE=media
      - QUEUE=intake:media
      - OUTPUT_QUEUE=extract:media

  # ═══════════════════════════════════════════════════════════════════════════
  # COMMUNICATION INTAKE (Email, Chat, Messenger)
  # ═══════════════════════════════════════════════════════════════════════════

  intake-comms:
    image: conductor-intake:comms
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 256M
    environment:
      - WORKER_TYPE=communications
      - QUEUE=intake:comms
      - OUTPUT_QUEUE=extract:comms
```

### Tier 2: Extraction Workers (Spezialisiert)

```yaml
  # ═══════════════════════════════════════════════════════════════════════════
  # PDF EXTRACTION - Dual-Path für Qualität
  # ═══════════════════════════════════════════════════════════════════════════

  # Fast Path: Tika für Text-PDFs
  extract-pdf-fast:
    image: apache/tika:latest
    deploy:
      replicas: 3
    environment:
      - MODE=text-only
      - MAX_FILE_SIZE=50MB

  # Slow Path: Docling für komplexe PDFs (Tabellen, Scans)
  extract-pdf-complex:
    image: conductor-docling:latest
    deploy:
      replicas: 2
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    environment:
      - MODE=full-analysis
      - ENABLE_TABLE_DETECTION=true
      - ENABLE_OCR_FALLBACK=true

  # ═══════════════════════════════════════════════════════════════════════════
  # AUDIO EXTRACTION - Tiered by Duration
  # ═══════════════════════════════════════════════════════════════════════════

  # Short Audio (<5 min): Schnell, CPU
  extract-audio-short:
    image: conductor-whisper:base
    deploy:
      replicas: 4
    environment:
      - MODEL=base
      - DEVICE=cpu
      - MAX_DURATION=300

  # Long Audio (>5 min): GPU, Large Model
  extract-audio-long:
    image: conductor-whisper:large-v3
    deploy:
      replicas: 1
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    environment:
      - MODEL=large-v3
      - DEVICE=cuda
      - ENABLE_VAD=true  # Voice Activity Detection

  # ═══════════════════════════════════════════════════════════════════════════
  # IMAGE EXTRACTION - OCR Pipeline
  # ═══════════════════════════════════════════════════════════════════════════

  # Stage 1: Preprocessing (Deskew, Denoise)
  extract-image-preprocess:
    image: conductor-imagemagick:latest
    deploy:
      replicas: 2

  # Stage 2: OCR (Multi-Engine für Accuracy)
  extract-image-ocr-tesseract:
    image: conductor-tesseract:5.5
    deploy:
      replicas: 3
    environment:
      - LANGUAGES=deu+eng
      - PSM=3  # Automatic page segmentation

  # Stage 3: OCR Verification (Confidence Check)
  extract-image-ocr-verify:
    image: conductor-paddleocr:latest
    deploy:
      replicas: 1
    environment:
      - MODE=verify-only
      - MIN_CONFIDENCE=0.85

  # ═══════════════════════════════════════════════════════════════════════════
  # VIDEO EXTRACTION - Parallel Streams
  # ═══════════════════════════════════════════════════════════════════════════

  # Audio Track → Whisper
  extract-video-audio:
    image: conductor-ffmpeg:latest
    command: ["extract-audio-track"]
    deploy:
      replicas: 2

  # Keyframes → OCR (für Text im Video)
  extract-video-keyframes:
    image: conductor-ffmpeg:latest
    command: ["extract-keyframes", "--interval", "10s"]
    deploy:
      replicas: 2

  # Metadata
  extract-video-metadata:
    image: conductor-mediainfo:latest
    deploy:
      replicas: 4
```

### Tier 3: Enrichment Workers (KI-intensiv)

```yaml
  # ═══════════════════════════════════════════════════════════════════════════
  # ENTITY EXTRACTION - Named Entity Recognition
  # ═══════════════════════════════════════════════════════════════════════════

  enrich-ner:
    image: conductor-gliner:latest
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G
    environment:
      - MODEL=urchade/gliner_medium-v2.1
      - ENTITY_TYPES=person,organization,location,date,money,email,phone

  # ═══════════════════════════════════════════════════════════════════════════
  # LANGUAGE DETECTION + TRANSLATION
  # ═══════════════════════════════════════════════════════════════════════════

  enrich-language:
    image: conductor-langdetect:latest
    deploy:
      replicas: 2

  enrich-translate:
    image: conductor-nllb:latest  # Meta's No Language Left Behind
    deploy:
      replicas: 1
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    environment:
      - TARGET_LANG=deu
      - SOURCE_LANGS=auto

  # ═══════════════════════════════════════════════════════════════════════════
  # CLASSIFICATION - Multi-Label
  # ═══════════════════════════════════════════════════════════════════════════

  enrich-classify:
    image: conductor-classifier:latest
    deploy:
      replicas: 2
    environment:
      - MODEL=local-llm
      - OLLAMA_URL=http://ollama-pool:11434

  # ═══════════════════════════════════════════════════════════════════════════
  # SENTIMENT + URGENCY DETECTION
  # ═══════════════════════════════════════════════════════════════════════════

  enrich-sentiment:
    image: conductor-sentiment:latest
    deploy:
      replicas: 2
    environment:
      - DETECT_URGENCY=true
      - DETECT_THREAT_LEVEL=true
```

### Tier 4: Index & Alert Workers

```yaml
  # ═══════════════════════════════════════════════════════════════════════════
  # SEARCH INDEX - Dual-Write
  # ═══════════════════════════════════════════════════════════════════════════

  index-fulltext:
    image: conductor-indexer:meilisearch
    deploy:
      replicas: 2
    environment:
      - TARGET=meilisearch:7700
      - BATCH_SIZE=100

  index-vector:
    image: conductor-indexer:qdrant
    deploy:
      replicas: 2
    environment:
      - TARGET=qdrant:6333
      - EMBEDDING_MODEL=multilingual-e5-large

  # ═══════════════════════════════════════════════════════════════════════════
  # ALERT ENGINE - Pattern Matching
  # ═══════════════════════════════════════════════════════════════════════════

  alert-patterns:
    image: conductor-alerter:latest
    deploy:
      replicas: 1
    environment:
      - RULES_PATH=/rules/patterns.yaml
      - NOTIFY_WEBHOOK=http://n8n:5678/webhook/alert
    volumes:
      - ./rules:/rules:ro
```

---

## Queue-Architektur (Redis Streams)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              REDIS STREAMS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  PRIORITY QUEUES                                                     │    │
│  ├──────────────────┬──────────────────┬──────────────────────────────┤    │
│  │  intake:priority │  intake:normal   │  intake:bulk                 │    │
│  │  (Real-time)     │  (< 1 hour)      │  (Background)                │    │
│  └──────────────────┴──────────────────┴──────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  TYPE-SPECIFIC QUEUES                                                │    │
│  ├──────────────────┬──────────────────┬──────────────────────────────┤    │
│  │  extract:pdf     │  extract:audio   │  extract:video               │    │
│  │  extract:image   │  extract:email   │  extract:archive             │    │
│  └──────────────────┴──────────────────┴──────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  PROCESSING QUEUES                                                   │    │
│  ├──────────────────┬──────────────────┬──────────────────────────────┤    │
│  │  enrich:ner      │  enrich:classify │  enrich:translate            │    │
│  │  index:fulltext  │  index:vector    │  alert:check                 │    │
│  └──────────────────┴──────────────────┴──────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ERROR HANDLING                                                      │    │
│  ├──────────────────┬──────────────────┬──────────────────────────────┤    │
│  │  dlq:extract     │  dlq:enrich      │  dlq:index                   │    │
│  │  (Dead Letter)   │  (Manual Review) │  (Retry 3x)                  │    │
│  └──────────────────┴──────────────────┴──────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Triage-Logik (Priority Scoring)

```python
def calculate_priority(file_metadata: dict) -> int:
    """
    Intelligence-Grade Triage: Welche Dateien zuerst?

    Score: 0-100 (höher = wichtiger)
    """
    score = 50  # Baseline

    # ══════════════════════════════════════════════════════════════════════════
    # RECENCY BOOST (Neue Dateien wichtiger)
    # ══════════════════════════════════════════════════════════════════════════
    age_hours = (now() - file_metadata['modified']).hours
    if age_hours < 1:
        score += 30      # Letzte Stunde: +30
    elif age_hours < 24:
        score += 20      # Letzter Tag: +20
    elif age_hours < 168:
        score += 10      # Letzte Woche: +10

    # ══════════════════════════════════════════════════════════════════════════
    # FILE TYPE WEIGHT (Kommunikation > Dokumente > Medien)
    # ══════════════════════════════════════════════════════════════════════════
    type_weights = {
        'email': 25,     # Kommunikation höchste Priorität
        'chat': 25,
        'pdf': 15,       # Dokumente mittel
        'docx': 15,
        'xlsx': 10,
        'image': 5,      # Medien niedrig
        'video': 5,
        'audio': 10,     # Audio höher (kann Gespräche sein)
    }
    score += type_weights.get(file_metadata['type'], 0)

    # ══════════════════════════════════════════════════════════════════════════
    # KEYWORD BOOST (Filename enthält wichtige Begriffe)
    # ══════════════════════════════════════════════════════════════════════════
    priority_keywords = [
        'vertrag', 'contract', 'rechnung', 'invoice',
        'passwort', 'password', 'geheim', 'secret',
        'steuer', 'tax', 'bank', 'konto', 'account'
    ]
    filename_lower = file_metadata['filename'].lower()
    for keyword in priority_keywords:
        if keyword in filename_lower:
            score += 15
            break

    # ══════════════════════════════════════════════════════════════════════════
    # SIZE PENALTY (Große Dateien später, außer sie sind wichtig)
    # ══════════════════════════════════════════════════════════════════════════
    size_mb = file_metadata['size'] / (1024 * 1024)
    if size_mb > 100 and score < 70:
        score -= 10  # Große unwichtige Dateien nach hinten

    return min(100, max(0, score))
```

---

## Dual-Path Processing (Fast vs. Deep)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DUAL-PATH PROCESSING                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INCOMING FILE                                                               │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────┐                                                            │
│  │   TRIAGE    │                                                            │
│  └──────┬──────┘                                                            │
│         │                                                                    │
│    ┌────┴────┐                                                              │
│    │         │                                                              │
│    ▼         ▼                                                              │
│ ┌──────┐  ┌──────┐                                                          │
│ │ FAST │  │ DEEP │                                                          │
│ │ PATH │  │ PATH │                                                          │
│ └──┬───┘  └──┬───┘                                                          │
│    │         │                                                              │
│    │         │                                                              │
│    ▼         ▼                                                              │
│ ┌──────────────────────────────────────────────────────────────────┐        │
│ │ FAST PATH (< 5 Sekunden)                                          │        │
│ ├──────────────────────────────────────────────────────────────────┤        │
│ │ • Tika Plain Text Extraction                                      │        │
│ │ • Basic NER (Regex + GLiNER)                                      │        │
│ │ • Keyword Classification                                          │        │
│ │ • Meilisearch Index                                               │        │
│ │                                                                    │        │
│ │ ERGEBNIS: Sofort durchsuchbar, grobe Klassifikation               │        │
│ └──────────────────────────────────────────────────────────────────┘        │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────┐        │
│ │ DEEP PATH (30+ Sekunden, Background)                              │        │
│ ├──────────────────────────────────────────────────────────────────┤        │
│ │ • Docling PDF Analysis (Tabellen, Layout)                         │        │
│ │ • Whisper Large-v3 (beste Transkription)                          │        │
│ │ • LLM-basierte Klassifikation                                     │        │
│ │ • Entity Resolution + Graph Building                              │        │
│ │ • Vector Embedding (Qdrant)                                       │        │
│ │                                                                    │        │
│ │ ERGEBNIS: Vollständige Analyse, ersetzt Fast-Path Ergebnisse      │        │
│ └──────────────────────────────────────────────────────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Optimierte docker-compose.yml

```yaml
version: '3.8'

# =============================================================================
# INTELLIGENCE-GRADE PROCESSING STACK
# =============================================================================

x-common-env: &common-env
  REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
  LOG_FORMAT: json
  LOG_LEVEL: INFO

x-worker-deploy: &worker-deploy
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3

services:

  # ===========================================================================
  # MESSAGE BROKER (Redis Streams)
  # ===========================================================================

  redis:
    image: redis:7.4-alpine
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
      --appendonly yes
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: 2G

  # ===========================================================================
  # ORCHESTRATOR (Job Distribution)
  # ===========================================================================

  orchestrator:
    build: ./docker/orchestrator
    environment:
      <<: *common-env
      PRIORITY_RULES: /rules/priority.yaml
    volumes:
      - ./rules:/rules:ro
    depends_on:
      - redis
    deploy:
      replicas: 2

  # ===========================================================================
  # INTAKE LAYER (File Type Detection + Routing)
  # ===========================================================================

  intake:
    build: ./docker/intake
    environment:
      <<: *common-env
      INPUT_QUEUE: intake:incoming
    volumes:
      - ${DATA_PATH}:/data:ro
    deploy:
      replicas: 3
      <<: *worker-deploy

  # ===========================================================================
  # EXTRACTION LAYER - Documents
  # ===========================================================================

  extract-tika:
    image: apache/tika:latest
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G

  extract-docling:
    build: ./docker/docling
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 8G
        reservations:
          devices:
            - capabilities: [gpu]

  # ===========================================================================
  # EXTRACTION LAYER - Audio/Video
  # ===========================================================================

  extract-whisper-fast:
    image: fedirz/faster-whisper-server:latest
    environment:
      WHISPER__MODEL: Systran/faster-whisper-base
      WHISPER__DEVICE: cpu
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G

  extract-whisper-accurate:
    image: fedirz/faster-whisper-server:latest-cuda
    environment:
      WHISPER__MODEL: Systran/faster-whisper-large-v3
      WHISPER__DEVICE: cuda
    deploy:
      replicas: 1
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  extract-ffmpeg:
    image: jrottenberg/ffmpeg:7-ubuntu
    entrypoint: ["tail", "-f", "/dev/null"]
    deploy:
      replicas: 2

  # ===========================================================================
  # EXTRACTION LAYER - Images (OCR Pipeline)
  # ===========================================================================

  extract-tesseract:
    image: jitesoft/tesseract-ocr:latest
    entrypoint: ["tail", "-f", "/dev/null"]
    deploy:
      replicas: 3

  extract-ocr-verify:
    build: ./docker/paddleocr
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 2G

  # ===========================================================================
  # ENRICHMENT LAYER
  # ===========================================================================

  enrich-ner:
    build: ./docker/gliner
    environment:
      <<: *common-env
      MODEL: urchade/gliner_medium-v2.1
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G

  enrich-classify:
    build: ./docker/classifier
    environment:
      <<: *common-env
      OLLAMA_URL: http://ollama:11434
    deploy:
      replicas: 2

  enrich-embeddings:
    build: ./docker/embedder
    environment:
      <<: *common-env
      MODEL: intfloat/multilingual-e5-large
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G

  # ===========================================================================
  # INDEX LAYER
  # ===========================================================================

  meilisearch:
    image: getmeili/meilisearch:latest
    environment:
      MEILI_MASTER_KEY: ${MEILI_MASTER_KEY}
      MEILI_ENV: production
    volumes:
      - meilisearch_data:/meili_data
    deploy:
      resources:
        limits:
          memory: 2G

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    deploy:
      resources:
        limits:
          memory: 2G

  index-writer:
    build: ./docker/indexer
    environment:
      <<: *common-env
      MEILISEARCH_URL: http://meilisearch:7700
      QDRANT_URL: http://qdrant:6333
    deploy:
      replicas: 2

  # ===========================================================================
  # LLM LAYER (GPU Pool)
  # ===========================================================================

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          devices:
            - capabilities: [gpu]

  # ===========================================================================
  # MONITORING & ALERTING
  # ===========================================================================

  alerter:
    build: ./docker/alerter
    environment:
      <<: *common-env
      RULES_PATH: /rules/alerts.yaml
      WEBHOOK_URL: ${ALERT_WEBHOOK}
    volumes:
      - ./rules:/rules:ro

  # ===========================================================================
  # API GATEWAY
  # ===========================================================================

  api-gateway:
    build: ./docker/conductor-api
    ports:
      - "8010:8000"
    environment:
      <<: *common-env
      MEILISEARCH_URL: http://meilisearch:7700
      QDRANT_URL: http://qdrant:6333
    deploy:
      replicas: 2

volumes:
  redis_data:
  meilisearch_data:
  qdrant_data:
  ollama_data:
```

---

## Kennzahlen-Vergleich

| Metrik | Consumer-Stack | Intelligence-Grade | Verbesserung |
|:-------|:---------------|:-------------------|:-------------|
| **Durchsatz** | 10 Dateien/min | 100+ Dateien/min | 10x |
| **Latenz (Fast Path)** | 30-60s | 2-5s | 10x |
| **Latenz (Deep Path)** | n/a | 30-120s | Background |
| **Fehlertoleranz** | Manual Restart | Auto-Recovery | ∞ |
| **Skalierung** | 1 Worker | N Workers | Linear |
| **Triage** | Keine | Priority Score | Wichtiges zuerst |

---

## Implementierungs-Empfehlung

### Phase 1: Queue-basierte Architektur
1. Redis Streams einführen
2. Intake Worker erstellen
3. Dead Letter Queue implementieren

### Phase 2: Dual-Path Processing
1. Fast Path für sofortige Durchsuchbarkeit
2. Deep Path für vollständige Analyse
3. Result Merging

### Phase 3: Horizontal Scaling
1. Worker-Replicas konfigurieren
2. Load Balancing
3. Auto-Scaling Rules

---

*Analyse basiert auf öffentlich verfügbaren Informationen über Intelligence Processing Architectures*
