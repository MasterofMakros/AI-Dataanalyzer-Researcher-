# Neural Vault Architecture

> **Version**: 2.0
> **Last Updated**: 2025-12-29

---

## System Overview

Neural Vault is an intelligence-grade document processing system designed for high-accuracy extraction of text, tables, and metadata from diverse document formats.

```
+------------------------------------------------------------------+
|                         CLIENTS                                   |
|  (Perplexica UI / API Consumers / Automated Pipelines)           |
+--------------------------------+---------------------------------+
                                 |
                    +------------v------------+
                    |      Traefik Proxy      |
                    |     (Load Balancer)     |
                    +------------+------------+
                                 |
         +-----------------------+-----------------------+
         |                       |                       |
+--------v--------+    +--------v--------+    +--------v--------+
|   REST API      |    |  Perplexica UI   |    |  Universal      |
|   (Port 8000)   |    |  (Port 3100)     |    |  Router (8030)  |
+-----------------+    +------------------+    +--------+--------+
                                                        |
                                               +--------v--------+
                                               |   Orchestrator  |
                                               |   (Port 8020)   |
                                               +--------+--------+
                                                        |
                         +------------------------------+------------------------------+
                         |                              |                              |
              +----------v----------+       +----------v----------+       +-----------v---------+
              |   Document Worker   |       |    Image Worker     |       |    Audio Worker     |
              |   (Documents)       |       |    (Images/Scans)   |       |    (Audio/Video)    |
              +----------+----------+       +----------+----------+       +-----------+---------+
                         |                              |                              |
                         +------------------------------+------------------------------+
                                                        |
                                           +------------v------------+
                                           |   Document Processor    |
                                           |      (Port 8005)        |
                                           |                         |
                                           |  +-------------------+  |
                                           |  | Docling (PDF)     |  |
                                           |  | Surya (OCR)       |  |
                                           |  | GLiNER (PII)      |  |
                                           |  | LanceDB (Vector)  |  |
                                           |  +-------------------+  |
                                           +-------------------------+
```

---

## Core Components

### 1. Universal Router (Port 8030)

**Purpose**: Intelligent file type detection and routing

**Capabilities**:
- Magic byte detection (200+ formats)
- MIME type validation
- Content-based routing decisions
- Extension fallback

**File**: `docker/universal-router/router.py`

```python
# Routing Logic
def detect_and_route(file_bytes, filename):
    # 1. Magic byte detection
    magic_type = magic.from_buffer(file_bytes[:2048])

    # 2. Route to appropriate processor
    if is_document(magic_type):
        return "document-processor/process/document"
    elif is_image(magic_type):
        return "document-processor/process/ocr"
    elif is_audio(magic_type):
        return "whisperx/transcribe"
```

### 2. Orchestrator (Port 8020)

**Purpose**: Job distribution and priority management

**Features**:
- Redis Streams for reliable queuing
- Priority-based job distribution
- Worker health monitoring
- Job retry and dead letter handling

**File**: `docker/orchestrator/orchestrator.py`

**Priority Queues**:
| Queue | SLA | Use Case |
|-------|-----|----------|
| `intake:priority` | < 5s | Interactive requests |
| `intake:normal` | < 30s | Standard processing |
| `intake:bulk` | Best effort | Batch operations |

### 3. Document Processor (Port 8005)

**Purpose**: Unified GPU-accelerated document processing

**Models**:
| Model | Task | Benchmark |
|-------|------|-----------|
| Docling | PDF/Office extraction | 97.9% table accuracy |
| Surya OCR | Image text recognition | 97.7% accuracy |
| GLiNER | PII/NER detection | Zero-shot capable |
| E5-Large | Embeddings | Multilingual |

**File**: `docker/document-processor/main.py`

**Endpoints**:
```
POST /process/document  - Auto-routing
POST /process/pdf       - Docling
POST /process/ocr       - Surya
POST /process/pii       - GLiNER
POST /vector/embed      - Embeddings
POST /vector/store      - LanceDB storage
POST /vector/search     - Semantic search
GET  /health            - Status
```

### 4. Extraction Workers

**Purpose**: Scalable processing workforce

**Types**:
- **DocumentWorker**: PDF, DOCX, PPTX, XLSX
- **ImageWorker**: JPG, PNG, TIFF, BMP
- **AudioWorker**: MP3, WAV, M4A, FLAC

**File**: `docker/workers/extraction_worker.py`

**Scaling**:
```bash
docker compose up -d --scale extraction-worker=5
```

---

## Data Flow

### Document Processing Flow

```
1. File Upload
   |
   v
2. Universal Router
   - Magic byte detection
   - Format validation
   - Route determination
   |
   v
3. Orchestrator
   - Priority assignment
   - Queue placement
   - Worker selection
   |
   v
4. Extraction Worker
   - Job claim
   - Processor invocation
   - Result handling
   |
   v
5. Document Processor
   - Model inference
   - Text extraction
   - PII detection
   - Embedding generation
   |
   v
6. Storage
   - LanceDB (vectors)
   - Redis (metadata)
   - Filesystem (original)
```

### Parser Selection Logic

```python
# Benchmark-driven selection
PARSER_CHAIN = {
    # Structured documents -> Docling first
    ".pdf":  [DOCLING, TIKA],      # 97.9% vs 75% tables
    ".docx": [DOCLING, TIKA],
    ".pptx": [DOCLING, TIKA],
    ".xlsx": [DOCLING, TIKA],

    # Images -> Surya first
    ".jpg":  [SURYA, TESSERACT],   # 97.7% vs 87%
    ".png":  [SURYA, TESSERACT],
    ".tiff": [SURYA, TESSERACT],

    # Audio/Video -> WhisperX
    ".mp3":  [WHISPERX],
    ".wav":  [WHISPERX],
    ".mp4":  [WHISPERX],

    # Plain text -> Tika
    ".txt":  [TIKA],
    ".html": [TIKA],
    ".xml":  [TIKA],
}
```

---

## Service Dependencies

```
                    +-------------+
                    |   Traefik   |
                    +------+------+
                           |
    +----------------------+----------------------+
    |                      |                      |
+---v---+            +-----v-----+          +-----v-----+
|  API  |            |    UI     |          |  Router   |
+---+---+            +-----------+          +-----+-----+
    |                                             |
    |            +--------------------------------+
    |            |
+---v------------v---+
|       Redis        |
+--------------------+
         ^
         |
+--------+--------+
|   Orchestrator  |
+--------+--------+
         |
+--------v--------+
|     Workers     |
+--------+--------+
         |
+--------v--------+
| Doc Processor   |
+-----------------+
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCUMENT_PROCESSOR_URL` | `http://document-processor:8000` | Processor endpoint |
| `REDIS_URL` | `redis://redis:6379` | Redis connection |
| `PROCESSOR_DEVICE` | `cuda` | GPU device |
| `SURYA_LANGS` | `de,en` | OCR languages |
| `LANCEDB_PATH` | `/data/lancedb` | Vector storage |
| `GLINER_MODEL` | `urchade/gliner_small-v2.1` | NER model |
| `EMBED_MODEL` | `intfloat/multilingual-e5-large` | Embedding model |

### Feature Flags

Located in `scripts/services/feature_flags.py`:

```python
FEATURE_FLAGS = {
    "USE_PARSER_ROUTING": True,    # Benchmark-driven selection
    "USE_SURYA_OCR": True,         # Surya over Tesseract
    "USE_WHISPERX": True,          # WhisperX for audio
    "USE_FALLBACK_CHAIN": True,    # Enable fallbacks
    "USE_PII_DETECTION": True,     # GLiNER PII
    "USE_VECTOR_STORE": True,      # LanceDB storage
}
```

---

## Deployment

### Development

```bash
# Start core services
docker compose up -d redis api ui

# Start processing pipeline
docker compose up -d document-processor universal-router orchestrator

# Start workers
docker compose up -d extraction-worker
```

### Production

```bash
# Full stack with scaling
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale workers based on load
docker compose up -d --scale extraction-worker=10

# GPU resource allocation
docker compose --profile gpu up -d
```

### Legacy Mode

```bash
# Include legacy services (Tesseract, old Whisper)
docker compose --profile legacy up -d
```

---

## Monitoring

### Health Checks

| Service | Endpoint | Interval |
|---------|----------|----------|
| Document Processor | `/health` | 30s |
| Universal Router | `/health` | 30s |
| Orchestrator | `/health` | 30s |
| Redis | `PING` | 10s |

### Metrics (Planned)

- Request latency (P50, P95, P99)
- Processing throughput (docs/min)
- Queue depth by priority
- Worker utilization
- Model inference time
- Error rates by type

---

## Security

### Network Isolation

- Internal Docker network for service communication
- Traefik as single entry point
- Tailscale for remote access

### Data Protection

- PII detection with GLiNER
- Automatic masking of sensitive data
- No persistent storage of raw uploads
- Temp file cleanup after processing

---

## Performance Tuning

### GPU Optimization

```yaml
# docker-compose.yml
document-processor:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            capabilities: [gpu]
  environment:
    - PROCESSOR_DEVICE=cuda
    - SURYA_BATCH_SIZE=4
    - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Memory Management

- Lazy model loading
- Explicit garbage collection between jobs
- CUDA cache clearing on shutdown
- Connection pooling for HTTP clients

---

## Troubleshooting

### Common Issues

**GPU not detected**:
```bash
docker run --rm --gpus all nvidia/cuda:12.1-base nvidia-smi
```

**Out of memory**:
```bash
# Reduce batch size
SURYA_BATCH_SIZE=2 docker compose up -d document-processor
```

**Slow processing**:
```bash
# Check worker count
docker compose ps extraction-worker

# Scale up
docker compose up -d --scale extraction-worker=5
```

**Queue backlog**:
```bash
# Check Redis streams
docker exec conductor-redis redis-cli XLEN intake:normal
```

---

## Neural Search Architecture

### Overview

Neural Search ist eine RAG-basierte Suchoberfläche (Retrieval-Augmented Generation), die natürlichsprachige Anfragen mit LLM-Synthese und Quellenverweisen beantwortet.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MISSION CONTROL UI                               │
│                         (React @ :3100)                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    NeuralSearchPage                              │   │
│  │  ┌─────────────────────────────────────────────────────────────┐│   │
│  │  │ PipelineStatusHeader - GPU/Worker/Queue Status              ││   │
│  │  ├─────────────────────────────────────────────────────────────┤│   │
│  │  │ SearchInput - Query + Keyboard Shortcuts (/, 1-9, Esc)      ││   │
│  │  ├─────────────────────────────────────────────────────────────┤│   │
│  │  │ SearchProgress - 4-Step Animation (Perplexity-Style)        ││   │
│  │  ├─────────────────────────────────────────────────────────────┤│   │
│  │  │ StreamingResponse - Answer mit Inline Citations (¹²³)       ││   │
│  │  ├─────────────────────────────────────────────────────────────┤│   │
│  │  │ SourceCard - Multi-Modal Preview (PDF/Audio/Image/Email)    ││   │
│  │  ├─────────────────────────────────────────────────────────────┤│   │
│  │  │ FollowUpSuggestions - 4 Related Questions                   ││   │
│  │  └─────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/SSE
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      NEURAL SEARCH API (:8040)                          │
│                                                                         │
│  POST /api/neural-search          ─── Synchrone RAG-Suche              │
│  POST /api/neural-search/stream   ─── SSE Streaming mit Fortschritt    │
│  GET  /api/pipeline/status        ─── Aggregierter Pipeline-Status     │
│  POST /api/neural-search/follow-ups ─ Follow-up Fragen generieren      │
│  GET  /api/sources/{id}           ─── Quell-Details                    │
│  GET  /api/sources/{id}/similar   ─── Ähnliche Quellen                 │
│                                                                         │
│  Abhängigkeiten:                                                        │
│  ├── Meilisearch (:7700) ─── Volltextsuche                             │
│  ├── Ollama (:11434)     ─── LLM-Synthese                              │
│  ├── Redis (:6379)       ─── Queue-Status                              │
│  └── Document Processor  ─── GPU-Status                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### Neural Search API (Port 8040)

**Purpose**: RAG-Suche mit LLM-generierter Antwort und Quellenverweisen

**File**: `docker/neural-search-api/neural_search_api.py`

**Endpoints**:
| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/api/neural-search` | POST | Synchrone Suche mit vollständiger Antwort |
| `/api/neural-search/stream` | POST | SSE-Streaming mit Echtzeit-Updates |
| `/api/pipeline/status` | GET | GPU/Worker/Queue/Index Status |
| `/api/neural-search/follow-ups` | POST | Verwandte Fragen generieren |
| `/api/sources/{id}` | GET | Quell-Details abrufen |

### SSE-Streaming-Protokoll

```
Event-Sequenz:
1. progress: {"step":"analyzing", "progress":10}
2. progress: {"step":"searching", "documentsFound":8}
3. sources:  [{...}, {...}]
4. progress: {"step":"reading", "currentSource":"doc.pdf"}
5. progress: {"step":"synthesizing"}
6. token:    "Dein "
7. token:    "Vertrag "
8. ...
9. complete: {"id":"...", "answer":"...", "citations":[...]}
10. followups: [{"question":"..."}, ...]
```

### UI-Komponenten

| Komponente | Datei | Zweck |
|------------|-------|-------|
| `NeuralSearchPage` | `NeuralSearchPage.tsx` | Hauptseite mit State-Management |
| `SearchProgress` | `SearchProgress.tsx` | 4-Schritt Fortschrittsanzeige |
| `StreamingResponse` | `StreamingResponse.tsx` | Antwort mit Citations |
| `SourceCard` | `SourceCard.tsx` | Multi-Modal Quellen-Preview |
| `FollowUpSuggestions` | `FollowUpSuggestions.tsx` | Related Questions |
| `PipelineStatusHeader` | `PipelineStatusHeader.tsx` | Status Bar |

### Datenmodelle

```typescript
interface SearchResponse {
  id: string;
  query: string;
  answer: string;           // Markdown mit ¹²³ Citations
  citations: Citation[];    // Mapping zu Sources
  sources: Source[];        // Multi-Modal Sources
  timestamp: Date;
  processingTimeMs: number;
}

interface Source {
  id: string;
  type: 'pdf' | 'audio' | 'image' | 'email' | 'video' | 'text';
  filename: string;
  confidence: number;       // 0-100
  excerpt: string;
  extractedVia: 'Docling' | 'Surya' | 'WhisperX' | 'Tika';
  // Typ-spezifische Felder...
}

interface PipelineStatus {
  gpuStatus: 'online' | 'offline' | 'busy';
  gpuModel: string;
  vramUsage: number;
  workersActive: number;
  queueDepth: number;
  indexedDocuments: number;
}
```

---

## Frontend Architecture

### Perplexica UI (Port 3100)

**Stack**: React 18 + TypeScript + Tailwind CSS + shadcn/ui

**Struktur**:
```
ui/perplexica/src/
├── App.tsx                      # Tab-Navigation (Search/Overview/Jobs/System)
├── components/
│   ├── neural-search/           # Neural Search Komponenten
│   └── ui/                      # shadcn/ui Base Components
├── types/
│   └── neural-search.ts         # TypeScript Interfaces
└── lib/
    └── utils.ts                 # Utility Functions
```

### nginx Reverse Proxy

**Routing-Priorität** (von spezifisch zu allgemein):
```nginx
1. /api/neural-search/*  → neural-search-api:8040
2. /api/pipeline/*       → neural-search-api:8040
3. /api/sources/*        → neural-search-api:8040
4. /api/status/*         → neural-search-api:8040
5. /api/*                → conductor-api:8000  (Fallback)
6. /*                    → Static Files (React SPA)
```

---

## Service Map (Complete)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          INFRASTRUCTURE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  Traefik (:8888)     │ Reverse Proxy, Load Balancer                     │
│  PostgreSQL (:5432)  │ n8n Database                                     │
│  Redis (:6379)       │ Queue, Cache, Streams                            │
├─────────────────────────────────────────────────────────────────────────┤
│                            STORAGE                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  Meilisearch (:7700) │ Full-Text Search Index                           │
│  Qdrant (:6333)      │ Vector Database                                  │
│  LanceDB             │ Embedded Vector Store                            │
├─────────────────────────────────────────────────────────────────────────┤
│                           AI MODELS                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Ollama (:11434)     │ LLM (llama3.2)                                   │
│  Document Processor  │ Docling, Surya, GLiNER, E5                       │
│  WhisperX (:9000)    │ Audio Transcription + Diarization                │
├─────────────────────────────────────────────────────────────────────────┤
│                          PROCESSING                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Universal Router    │ File Detection & Routing (:8030)                 │
│  Orchestrator        │ Job Distribution (:8020)                         │
│  Extraction Workers  │ Scalable Processing Pool                         │
│  Document Processor  │ GPU-Accelerated Processing (:8005)               │
├─────────────────────────────────────────────────────────────────────────┤
│                             APIs                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  Conductor API       │ Legacy REST API (:8010)                          │
│  Neural Search API   │ RAG + LLM Synthesis (:8040)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                           FRONTEND                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  Perplexica UI       │ React UI (:3100)                                 │
└─────────────────────────────────────────────────────────────────────────┘
```
