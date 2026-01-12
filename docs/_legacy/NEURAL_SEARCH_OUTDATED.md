# Neural Search - Implementierungsdokumentation

> Vollständige technische Dokumentation der Neural Search Komponente für Agentensysteme

---

## Inhaltsverzeichnis

1. [Systemübersicht](#systemübersicht)
2. [Architektur](#architektur)
3. [Frontend-Komponenten](#frontend-komponenten)
4. [Backend-API](#backend-api)
5. [Datenmodelle](#datenmodelle)
6. [SSE-Streaming-Protokoll](#sse-streaming-protokoll)
7. [Docker-Konfiguration](#docker-konfiguration)
8. [Erweiterungspunkte](#erweiterungspunkte)

---

## Systemübersicht

Neural Search ist eine Perplexity-inspirierte RAG-Suchoberfläche (Retrieval-Augmented Generation), die:

- **Dokumente durchsucht** via Meilisearch
- **LLM-Synthese** mit Quellenverweisen via Ollama generiert
- **Multi-modale Quellen** unterstützt (PDF, Audio, Bilder, E-Mails)
- **Echtzeit-Streaming** der Antworten via SSE bietet
- **Pipeline-Status** in Echtzeit anzeigt

### Technologie-Stack

| Komponente | Technologie | Port |
|------------|-------------|------|
| Frontend | React + TypeScript + Tailwind | 3000 |
| Neural Search API | FastAPI + Python | 8040 |
| Suchindex | Meilisearch | 7700 |
| LLM | Ollama (llama3.2) | 11434 |
| Cache/Queue | Redis | 6379 |
| Reverse Proxy | nginx | 3000 |

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MISSION CONTROL UI                               │
│                         (React @ :3000)                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │   Search    │ │  Overview   │ │    Jobs     │ │   System    │       │
│  │    Tab      │ │    Tab      │ │    Tab      │ │    Tab      │       │
│  └──────┬──────┘ └─────────────┘ └─────────────┘ └─────────────┘       │
│         │                                                               │
│  ┌──────▼──────────────────────────────────────────────────────────┐   │
│  │                    NeuralSearchPage                              │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │ PipelineStatusHeader (GPU/Worker/Queue/Index Status)       │ │   │
│  │  ├────────────────────────────────────────────────────────────┤ │   │
│  │  │ SearchInput (Query + Keyboard Shortcuts)                   │ │   │
│  │  ├────────────────────────────────────────────────────────────┤ │   │
│  │  │ SearchProgress (4-Step Animation)                          │ │   │
│  │  ├────────────────────────────────────────────────────────────┤ │   │
│  │  │ StreamingResponse (Answer + Citations + Source Pills)      │ │   │
│  │  ├────────────────────────────────────────────────────────────┤ │   │
│  │  │ SourceCard (PDF/Audio/Image/Email Preview)                 │ │   │
│  │  ├────────────────────────────────────────────────────────────┤ │   │
│  │  │ FollowUpSuggestions (4 Related Questions)                  │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/SSE
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           NGINX REVERSE PROXY                           │
│  /api/neural-search/* ──────────▶ neural-search-api:8040               │
│  /api/pipeline/*      ──────────▶ neural-search-api:8040               │
│  /api/sources/*       ──────────▶ neural-search-api:8040               │
│  /api/status/*        ──────────▶ neural-search-api:8040               │
│  /api/*               ──────────▶ conductor-api:8000                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      NEURAL SEARCH API (:8040)                          │
│                                                                         │
│  POST /api/neural-search          ─── Non-Streaming RAG Search         │
│  POST /api/neural-search/stream   ─── SSE Streaming RAG Search         │
│  GET  /api/pipeline/status        ─── Aggregated Pipeline Status       │
│  POST /api/neural-search/follow-ups ─ Generate Follow-up Questions     │
│  GET  /api/sources/{id}           ─── Source Details                   │
│  GET  /api/sources/{id}/similar   ─── Similar Sources                  │
│                                                                         │
│  Abhängigkeiten:                                                        │
│  ├── Meilisearch (:7700) ─── Dokumentensuche                           │
│  ├── Ollama (:11434)     ─── LLM-Synthese                              │
│  ├── Redis (:6379)       ─── Queue-Status                              │
│  └── Document Processor  ─── GPU-Status                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Frontend-Komponenten

### Dateistruktur

```
ui/perplexica/src/
├── components/
│   ├── neural-search/
│   │   ├── index.ts                 # Exports
│   │   ├── NeuralSearchPage.tsx     # Hauptseite
│   │   ├── SearchProgress.tsx       # 4-Step Animation
│   │   ├── StreamingResponse.tsx    # Antwort mit Citations
│   │   ├── SourceCard.tsx           # Multi-Modal Source Preview
│   │   ├── FollowUpSuggestions.tsx  # Related Questions
│   │   └── PipelineStatusHeader.tsx # Status Bar
│   └── ui/                          # shadcn/ui Komponenten
├── types/
│   ├── index.ts
│   └── neural-search.ts             # TypeScript Interfaces
└── App.tsx                          # Legacy tab navigation (historical)
```

### Komponenten-Details

#### 1. NeuralSearchPage.tsx

**Zweck:** Hauptcontainer für die Neural Search Funktionalität

**State:**
```typescript
const [query, setQuery] = useState('');                    // Suchquery
const [isSearching, setIsSearching] = useState(false);     // Suchstatus
const [searchProgress, setSearchProgress] = useState();    // Fortschritt
const [response, setResponse] = useState();                // Vollständige Antwort
const [sources, setSources] = useState([]);                // Gefundene Quellen
const [followUps, setFollowUps] = useState([]);            // Follow-up Fragen
const [streamedAnswer, setStreamedAnswer] = useState('');  // Streaming-Text
const [pipelineStatus, setPipelineStatus] = useState();    // Pipeline-Status
```

**Keyboard Shortcuts:**
| Taste | Aktion |
|-------|--------|
| `/` | Suchfeld fokussieren |
| `1-9` | Quelle öffnen |
| `Esc` | Suche abbrechen / Quelle schließen |

**API-Aufrufe:**
```typescript
// Streaming-Suche
fetch('/api/neural-search/stream', {
  method: 'POST',
  body: JSON.stringify({ query, limit: 8 })
})

// Pipeline-Status (alle 5s)
fetch('/api/pipeline/status')
```

#### 2. SearchProgress.tsx

**Zweck:** Animierter 4-Schritt-Fortschritt während der Suche

**Steps:**
1. `analyzing` - Query analysieren, Keywords extrahieren
2. `searching` - Meilisearch durchsuchen
3. `reading` - Relevante Quellen lesen
4. `synthesizing` - LLM-Antwort generieren

**Props:**
```typescript
interface SearchProgressProps {
  progress: {
    step: 'analyzing' | 'searching' | 'reading' | 'synthesizing' | 'complete';
    progress: number;           // 0-100
    keywords?: string[];        // Extrahierte Keywords
    documentsFound?: number;    // Gefundene Dokumente
    documentsTotal?: number;    // Gesamtanzahl im Index
    currentSource?: string;     // Aktuell gelesene Quelle
    sourcesRead?: number;       // Gelesene Quellen
    sourcesTotal?: number;      // Zu lesende Quellen
  }
}
```

#### 3. StreamingResponse.tsx

**Zweck:** Antwortanzeige mit Inline-Citations und Quellen-Pills

**Features:**
- Markdown-Rendering mit **fett** und `code`
- Superscript-Citations (¹²³) als klickbare Buttons
- Hover-Effekte synchronisiert zwischen Text und Quellen
- Konfidenz-Badges für jede Quelle

**Props:**
```typescript
interface StreamingResponseProps {
  answer: string;                              // Markdown-Text mit ¹²³
  citations: Citation[];                       // Citation-Mappings
  sources: Source[];                           // Vollständige Quellen
  isStreaming: boolean;                        // Cursor blinkt
  timestamp?: Date;                            // Antwort-Zeit
  onSourceClick: (sourceId: string) => void;   // Quelle öffnen
  onCitationHover: (index: number | null) => void; // Highlight sync
}
```

#### 4. SourceCard.tsx

**Zweck:** Multi-modale Quellen-Preview mit typ-spezifischen Features

**Unterstützte Typen:**
| Typ | Features |
|-----|----------|
| `pdf` | Seite, Zeile, Highlighted Text |
| `audio` | Waveform, Timestamp, Transcript mit Diarization |
| `image` | Bounding Box, OCR-Text |
| `email` | Von/Betreff Header, Content |
| `video` | Timestamp, Duration |
| `text` | Plain Text |

**Actions:**
- Original öffnen
- Text kopieren
- Ähnliche finden
- Verifizieren

#### 5. PipelineStatusHeader.tsx

**Zweck:** Echtzeit-Statusanzeige der Pipeline-Komponenten

**Angezeigte Metriken:**
- GPU Status (online/offline/busy) + VRAM %
- Workers (aktiv/total)
- Queue Depth
- Indexed Documents
- Last Sync Time

---

## Backend-API

### Dateistruktur

```
docker/neural-search-api/
├── Dockerfile
├── requirements.txt
└── neural_search_api.py    # ~450 Zeilen
```

### Endpoints

#### POST /api/neural-search

**Beschreibung:** Synchrone RAG-Suche mit vollständiger Antwort

**Request:**
```json
{
  "query": "Was weiß ich über meinen Telekom-Vertrag?",
  "limit": 8,
  "filters": {}
}
```

**Response:**
```json
{
  "id": "a1b2c3d4e5f6",
  "query": "Was weiß ich über meinen Telekom-Vertrag?",
  "answer": "Dein Telekom-Vertrag **Magenta M** läuft seit **15. März 2022** ¹...",
  "citations": [
    {"index": 1, "sourceId": "src_001", "text": "Vertragsbeginn 15.03.2022"}
  ],
  "sources": [
    {
      "id": "src_001",
      "type": "pdf",
      "filename": "Telekom_Vertrag_2022.pdf",
      "confidence": 98,
      "excerpt": "...",
      "extractedVia": "Docling"
    }
  ],
  "timestamp": "2025-01-15T14:32:00Z",
  "processingTimeMs": 3500
}
```

#### POST /api/neural-search/stream

**Beschreibung:** SSE-Streaming RAG-Suche mit Echtzeit-Updates

**Event-Types:**
| Event | Data | Beschreibung |
|-------|------|--------------|
| `progress` | `SearchProgress` | Fortschritts-Updates |
| `sources` | `Source[]` | Gefundene Quellen |
| `token` | `string` | Einzelnes Antwort-Token |
| `complete` | `SearchResponse` | Vollständige Antwort |
| `followups` | `FollowUpQuestion[]` | Verwandte Fragen |

#### GET /api/pipeline/status

**Response:**
```json
{
  "gpuStatus": "online",
  "gpuModel": "RTX 5090",
  "vramUsage": 48,
  "workersActive": 3,
  "workersTotal": 3,
  "queueDepth": 18,
  "indexedDocuments": 12453,
  "lastSync": "2025-01-15T14:30:00Z"
}
```

---

## Datenmodelle

### TypeScript Interfaces (types/neural-search.ts)

```typescript
// Suchfortschritt
interface SearchProgress {
  step: 'analyzing' | 'searching' | 'reading' | 'synthesizing' | 'complete';
  progress: number;
  keywords?: string[];
  documentsFound?: number;
  documentsTotal?: number;
  currentSource?: string;
  sourcesRead?: number;
  sourcesTotal?: number;
}

// Quelle
interface Source {
  id: string;
  type: 'pdf' | 'audio' | 'image' | 'email' | 'video' | 'text';
  filename: string;
  path: string;
  confidence: number;           // 0-100
  excerpt: string;
  highlightedText?: string;
  page?: number;                // PDF
  line?: string;                // PDF
  timestamp?: string;           // Audio/Video "HH:MM:SS"
  duration?: string;            // Audio/Video
  speakers?: string[];          // Audio Diarization
  transcript?: TranscriptLine[];// Audio
  boundingBox?: BoundingBox;    // Image OCR
  extractedVia: string;         // 'Docling' | 'Surya' | 'WhisperX' | 'Tika'
}

// Citation im Antwort-Text
interface Citation {
  index: number;      // 1-9 (für ¹²³)
  sourceId: string;   // Referenz auf Source.id
  text: string;       // Snippet aus der Quelle
}

// Vollständige Suchantwort
interface SearchResponse {
  id: string;
  query: string;
  answer: string;              // Markdown mit ¹²³ Citations
  citations: Citation[];
  sources: Source[];
  timestamp: Date;
  processingTimeMs: number;
}

// Pipeline-Status
interface PipelineStatus {
  gpuStatus: 'online' | 'offline' | 'busy';
  gpuModel: string;
  vramUsage: number;
  workersActive: number;
  workersTotal: number;
  queueDepth: number;
  indexedDocuments: number;
  lastSync: Date;
}
```

---

## SSE-Streaming-Protokoll

### Event-Sequenz

```
Client                              Server
  │                                   │
  │  POST /api/neural-search/stream   │
  │ ────────────────────────────────▶ │
  │                                   │
  │  event: progress                  │
  │  data: {"step":"analyzing",...}   │
  │ ◀──────────────────────────────── │
  │                                   │
  │  event: progress                  │
  │  data: {"step":"searching",...}   │
  │ ◀──────────────────────────────── │
  │                                   │
  │  event: sources                   │
  │  data: [{...}, {...}]             │
  │ ◀──────────────────────────────── │
  │                                   │
  │  event: progress                  │
  │  data: {"step":"reading",...}     │
  │ ◀──────────────────────────────── │
  │                                   │
  │  event: progress                  │
  │  data: {"step":"synthesizing",...}│
  │ ◀──────────────────────────────── │
  │                                   │
  │  event: token                     │
  │  data: "Dein "                    │
  │ ◀──────────────────────────────── │
  │  event: token                     │
  │  data: "Telekom-"                 │
  │ ◀──────────────────────────────── │
  │  ... (viele tokens) ...           │
  │                                   │
  │  event: complete                  │
  │  data: {"id":"...","answer":"..."}│
  │ ◀──────────────────────────────── │
  │                                   │
  │  event: followups                 │
  │  data: [{"question":"..."}]       │
  │ ◀──────────────────────────────── │
  │                                   │
```

### Client-Side Parsing

```typescript
const reader = res.body?.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';

  for (const line of lines) {
    if (line.startsWith('event:')) {
      // Event-Typ merken
    }
    if (line.startsWith('data:')) {
      const data = JSON.parse(line.substring(5));
      // Event verarbeiten...
    }
  }
}
```

---

## Docker-Konfiguration

### docker-compose.yml (Auszug)

```yaml
neural-search-api:
  build:
    context: ./docker/neural-search-api
    dockerfile: Dockerfile
  image: neural-search-api:latest
  container_name: conductor-neural-search
  ports:
    - "8040:8040"
  environment:
    - MEILISEARCH_URL=http://meilisearch:7700
    - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
    - OLLAMA_URL=http://ollama:11434
    - OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.2}
    - REDIS_HOST=redis
    - REDIS_PASSWORD=${REDIS_PASSWORD}
  depends_on:
    - meilisearch
    - redis
    - ollama

perplexica:
  build:
    context: ui/perplexica
    dockerfile: Dockerfile
  ports:
    - "3100:3000"
  depends_on:
    - conductor-api
    - neural-search-api
```

### nginx.conf (Routing)

```nginx
# Neural Search API (RAG + LLM) - Muss VOR /api/ kommen!
location /api/neural-search {
    proxy_pass http://neural-search-api:8040/api/neural-search;
    proxy_buffering off;      # Wichtig für SSE
    proxy_cache off;
    chunked_transfer_encoding on;
}

location /api/pipeline/ {
    proxy_pass http://neural-search-api:8040/api/pipeline/;
}

location /api/sources/ {
    proxy_pass http://neural-search-api:8040/api/sources/;
}

# Legacy API (Fallback)
location /api/ {
    proxy_pass http://conductor-api:8000/;
}
```

---

## Erweiterungspunkte

### Neue Quelltypen hinzufügen

1. **types/neural-search.ts:** SourceType erweitern
```typescript
type SourceType = 'pdf' | 'audio' | 'image' | 'email' | 'video' | 'text' | 'neuerTyp';
```

2. **SourceCard.tsx:** Neue Preview-Komponente
```typescript
{source.type === 'neuerTyp' && <NeuerTypPreview source={source} />}
```

3. **neural_search_api.py:** Typ-Erkennung
```python
def detect_source_type(filename: str) -> str:
    if filename.endswith('.neu'):
        return 'neuerTyp'
```

### Neue LLM-Provider

In `neural_search_api.py`:

```python
async def generate_llm_response(query: str, sources: List[Source]):
    if LLM_PROVIDER == 'ollama':
        # Bestehendes Ollama
    elif LLM_PROVIDER == 'openai':
        # OpenAI-kompatible API
    elif LLM_PROVIDER == 'anthropic':
        # Claude API
```

### Zusätzliche Suchindizes

```python
async def search_meilisearch(query: str, limit: int):
    indices = ['documents', 'emails', 'transcripts']
    all_hits = []
    for idx_name in indices:
        hits = meili_client.index(idx_name).search(query)
        all_hits.extend(hits)
    return merge_and_rank(all_hits)
```

---

## Bekannte Limitierungen

1. **Ollama Cold Start:** Erste Anfrage kann 10-30s dauern
2. **SSE über nginx:** `proxy_buffering off` erforderlich
3. **Citation-Parsing:** Nur ¹-⁹ unterstützt (max 9 Quellen)
4. **Audio-Player:** Nur Placeholder, echtes Audio-Playback fehlt

---

## Wartung & Debugging

### Logs prüfen

```bash
# Neural Search API Logs
docker logs conductor-neural-search -f

# UI Build Logs
docker logs conductor-ui

# Alle Services
docker compose logs -f
```

### Health Checks

```bash
# Neural Search API
curl http://localhost:8040/health

# Pipeline Status
curl http://localhost:8040/api/pipeline/status

# Meilisearch
curl http://localhost:7700/health
```

### Häufige Probleme

| Problem | Ursache | Lösung |
|---------|---------|--------|
| "Keine Ergebnisse" | Meilisearch leer | Dokumente indexieren |
| SSE-Timeout | nginx buffering | `proxy_buffering off` |
| LLM-Fehler | Ollama nicht gestartet | `docker compose up -d ollama` |
| CORS-Fehler | nginx config | Prüfe `Access-Control-*` Header |

---

*Dokumentation erstellt: 2025-01-15*
*Version: 1.0.0*
