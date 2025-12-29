# Neural Vault - Mission Control UI Concept 2025

## Overview

Die neue Mission Control UI visualisiert die Intelligence-Grade Pipeline mit Echtzeit-Status aller Komponenten.

---

## 1. Dashboard Layout

```
+-----------------------------------------------------------------------------------+
|  NEURAL VAULT                                              [GPU] RTX 5090  14:32  |
|  Mission Control v2.0                                      [===] 48% VRAM         |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [Overview]  [Pipeline]  [Jobs]  [Search]  [Settings]                            |
|                                                                                   |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +------ SYSTEM ARCHITECTURE ------------------------------------------------+   |
|  |                                                                           |   |
|  |    +-------+      +--------+      +-----------+      +--------+          |   |
|  |    |  F:\  | ---> | Router | ---> | Orchestr. | ---> | Workers|          |   |
|  |    | 7.2TB |      | :8030  |      |   :8020   |      |  x 3   |          |   |
|  |    +-------+      +--------+      +-----------+      +--------+          |   |
|  |        |                               |                  |              |   |
|  |        v                               v                  v              |   |
|  |   +---------+                   +------------+      +-----------+        |   |
|  |   | Meili   |                   |   Redis    |      | Doc Proc  |        |   |
|  |   | Search  |                   |  Streams   |      | GPU :8005 |        |   |
|  |   +---------+                   +------------+      +-----------+        |   |
|  |                                                           |              |   |
|  |                                                           v              |   |
|  |                                                     +-----------+        |   |
|  |                                                     | LanceDB   |        |   |
|  |                                                     | Vectors   |        |   |
|  |                                                     +-----------+        |   |
|  +-----------------------------------------------------------------------+   |
|                                                                                   |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +---- QUEUES ----------+  +---- PROCESSOR --------+  +---- HEALTH -----------+  |
|  |                      |  |                       |  |                        |  |
|  |  Priority    [##  ] 2|  |  Mode: GPU (CUDA)     |  |  Router      [online]  |  |
|  |  Normal    [####  ] 4|  |  Docling    [loaded]  |  |  Orchestr.   [online]  |  |
|  |  Bulk     [######] 12|  |  Surya OCR  [loaded]  |  |  DocProc     [online]  |  |
|  |                      |  |  GLiNER     [ready ]  |  |  WhisperX    [online]  |  |
|  |  Total: 18 jobs      |  |  E5-Large   [ready ]  |  |  Meilisearch [online]  |  |
|  |                      |  |                       |  |  Redis       [online]  |  |
|  +----------------------+  +-----------------------+  +------------------------+  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Pipeline View (Tab: Pipeline)

```
+-----------------------------------------------------------------------------------+
|  NEURAL VAULT                                              [GPU] RTX 5090  14:32  |
+-----------------------------------------------------------------------------------+
|  [Overview]  [Pipeline]  [Jobs]  [Search]  [Settings]                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +---- FILE INTAKE ----+     +---- DETECTION ----+     +---- ROUTING ----+       |
|  |                     |     |                   |     |                 |       |
|  |  Watching: F:\      | --> | Magic Bytes: OK   | --> | PDF  -> Docling |       |
|  |                     |     |                   |     | IMG  -> Surya   |       |
|  |  New files: 3       |     | MIME: application |     | Audio-> WhisperX|       |
|  |  Pending:   12      |     |       /pdf        |     | Other-> Tika    |       |
|  |                     |     |                   |     |                 |       |
|  +---------------------+     +-------------------+     +-----------------+       |
|           |                          |                         |                 |
|           v                          v                         v                 |
|  +------ PROCESSING PIPELINE ------------------------------------------------+   |
|  |                                                                           |   |
|  |  intake:priority ----+                                                    |   |
|  |        [##]  2 jobs  |    +-------------+    +-------------+             |   |
|  |                      +--> |   Worker 1  | -> | Doc Process | -> Results  |   |
|  |  intake:normal ------+    | (documents) |    | (Docling)   |             |   |
|  |       [####]  4 jobs |    +-------------+    +-------------+             |   |
|  |                      |                                                    |   |
|  |  intake:bulk --------+    +-------------+    +-------------+             |   |
|  |      [######] 12 jobs+--> |   Worker 2  | -> | Doc Process | -> Results  |   |
|  |                      |    |  (images)   |    | (Surya OCR) |             |   |
|  |                      |    +-------------+    +-------------+             |   |
|  |                      |                                                    |   |
|  |                      |    +-------------+    +-------------+             |   |
|  |                      +--> |   Worker 3  | -> | WhisperX    | -> Results  |   |
|  |                           |   (audio)   |    | (Transcr.)  |             |   |
|  |                           +-------------+    +-------------+             |   |
|  |                                                                           |   |
|  +-----------------------------------------------------------------------+   |
|                                                                                   |
|  +---- ENRICHMENT ----+     +---- STORAGE -----+     +---- OUTPUT ----+          |
|  |                    |     |                  |     |                |          |
|  |  PII Detection     | --> | LanceDB Vectors  | --> | Meilisearch   |          |
|  |  GLiNER NER        |     | (Embeddings)     |     | (Full-Text)   |          |
|  |                    |     |                  |     |                |          |
|  +--------------------+     +------------------+     +----------------+          |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 3. Jobs View (Tab: Jobs)

```
+-----------------------------------------------------------------------------------+
|  NEURAL VAULT                                              [GPU] RTX 5090  14:32  |
+-----------------------------------------------------------------------------------+
|  [Overview]  [Pipeline]  [Jobs]  [Search]  [Settings]                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  Filter: [All v]  Status: [All v]  Type: [All v]        [+ Submit Job] [Refresh] |
|                                                                                   |
|  +-----------------------------------------------------------------------+       |
|  | ID          | Type      | File                    | Status   | Time   |       |
|  +-----------------------------------------------------------------------+       |
|  | job-a1b2c3  | PDF       | Vertrag_2024.pdf        | [=====]  | 2.3s   |       |
|  |             | Docling   | F:\Inbox\...            | done     |        |       |
|  +-----------------------------------------------------------------------+       |
|  | job-d4e5f6  | Image     | Scan_0042.jpg           | [====.]  | 1.8s   |       |
|  |             | Surya OCR | F:\Inbox\Scans\...      | process  |        |       |
|  +-----------------------------------------------------------------------+       |
|  | job-g7h8i9  | Audio     | Interview_Max.mp3       | [==...]  | 45.2s  |       |
|  |             | WhisperX  | F:\Audio\...            | process  |        |       |
|  +-----------------------------------------------------------------------+       |
|  | job-j0k1l2  | PDF       | Report_Q4.pdf           | [....]   | -      |       |
|  |             | Docling   | F:\Reports\...          | queued   |        |       |
|  +-----------------------------------------------------------------------+       |
|  | job-m3n4o5  | DOCX      | Brief_Anwalt.docx       | [XXXXX]  | 0.5s   |       |
|  |             | Docling   | F:\Korrespondenz\...    | failed   | retry  |       |
|  +-----------------------------------------------------------------------+       |
|                                                                                   |
|  Showing 5 of 18 jobs                              [< Prev] [1] [2] [3] [Next >] |
|                                                                                   |
+-----------------------------------------------------------------------------------+
|  +---- JOB DETAILS (job-a1b2c3) ---------------------------------------------+   |
|  |                                                                           |   |
|  |  File: Vertrag_2024.pdf                                                   |   |
|  |  Path: F:\Inbox\Vertraege\Vertrag_2024.pdf                               |   |
|  |  Size: 2.4 MB | Pages: 12 | Tables: 3                                    |   |
|  |                                                                           |   |
|  |  Processor: Docling (97.9% confidence)                                   |   |
|  |  Duration: 2.3s | Extracted: 4,521 chars                                 |   |
|  |                                                                           |   |
|  |  PII Detected: 2 entities                                                |   |
|  |    - PERSON: "Max Mustermann" (score: 0.94)                              |   |
|  |    - IBAN: "DE89 3704 0044 0532 0130 00" (score: 0.98)                   |   |
|  |                                                                           |   |
|  |  [View Text] [View Markdown] [Download] [Reprocess]                      |   |
|  +-----------------------------------------------------------------------+   |
+-----------------------------------------------------------------------------------+
```

---

## 4. Document Processor Status Panel

```
+-----------------------------------------------------------------------------------+
|  DOCUMENT PROCESSOR                                        [GPU Mode]  :8005     |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +---- GPU STATUS ----+     +---- MODELS LOADED ----+     +---- STATS ----+      |
|  |                    |     |                       |     |               |      |
|  |  Device: RTX 5090  |     |  [*] Docling          |     |  Processed:   |      |
|  |  VRAM: 12.4/24 GB  |     |      DocumentConv.    |     |    1,234 docs |      |
|  |  Util:  67%        |     |                       |     |               |      |
|  |                    |     |  [*] Surya OCR        |     |  Avg Time:    |      |
|  |  Temp:  62C        |     |      det + rec model  |     |    2.1s/doc   |      |
|  |  Power: 285W       |     |                       |     |               |      |
|  |                    |     |  [*] GLiNER           |     |  Errors:      |      |
|  |                    |     |      medium-v2.1      |     |    12 (0.9%)  |      |
|  |                    |     |                       |     |               |      |
|  |                    |     |  [*] E5-Large         |     |  Uptime:      |      |
|  |                    |     |      1024-dim embed   |     |    4d 12h 33m |      |
|  +--------------------+     +-----------------------+     +---------------+      |
|                                                                                   |
|  +---- PROCESSING BREAKDOWN -------------------------------------------------+   |
|  |                                                                           |   |
|  |  PDF (Docling)     [========================] 847  (68.6%)               |   |
|  |  Images (Surya)    [=======                 ] 234  (19.0%)               |   |
|  |  Office (Docling)  [===                     ] 98   (7.9%)                |   |
|  |  Audio (WhisperX)  [==                      ] 55   (4.5%)                |   |
|  |                                                                           |   |
|  +-----------------------------------------------------------------------+   |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 5. Search View (Tab: Search)

```
+-----------------------------------------------------------------------------------+
|  NEURAL VAULT                                              [GPU] RTX 5090  14:32  |
+-----------------------------------------------------------------------------------+
|  [Overview]  [Pipeline]  [Jobs]  [Search]  [Settings]                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +---- SEMANTIC SEARCH ------------------------------------------------------+   |
|  |                                                                           |   |
|  |  [                                                              ] [Search]|   |
|  |                                                                           |   |
|  |  Mode: [Hybrid v]    Limit: [10 v]    Filter: [All Types v]              |   |
|  |                                                                           |   |
|  +-----------------------------------------------------------------------+   |
|                                                                                   |
|  Query: "Mietvertrag mit Kaution uber 2000 Euro"                                 |
|                                                                                   |
|  +---- RESULTS (8 found) ----------------------------------------------------+   |
|  |                                                                           |   |
|  |  1. [0.94] Mietvertrag_Hauptstr_15.pdf                                   |   |
|  |     "...Kaution in Hohe von 2.400 EUR wird bei Einzug fallig..."         |   |
|  |     Path: F:\Vertraege\Miete\                                            |   |
|  |     [Open] [Details] [Similar]                                           |   |
|  |                                                                           |   |
|  |  2. [0.89] Mietvertrag_Nebenkosten_2023.pdf                              |   |
|  |     "...Kautionszahlung gemaess Paragraph 3: EUR 1.800..."               |   |
|  |     Path: F:\Vertraege\Miete\                                            |   |
|  |     [Open] [Details] [Similar]                                           |   |
|  |                                                                           |   |
|  |  3. [0.82] Wohnungsuebergabe_Protokoll.pdf                               |   |
|  |     "...Kaution vollstandig zurueckgezahlt, Betrag: 2.000 EUR..."        |   |
|  |     Path: F:\Dokumente\Wohnung\                                          |   |
|  |     [Open] [Details] [Similar]                                           |   |
|  |                                                                           |   |
|  +-----------------------------------------------------------------------+   |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 6. Settings View (Tab: Settings)

```
+-----------------------------------------------------------------------------------+
|  NEURAL VAULT                                              [GPU] RTX 5090  14:32  |
+-----------------------------------------------------------------------------------+
|  [Overview]  [Pipeline]  [Jobs]  [Search]  [Settings]                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +---- FEATURE FLAGS --------------------------------------------------------+   |
|  |                                                                           |   |
|  |  Processor Selection                                                      |   |
|  |  [x] USE_SURYA_OCR        Surya statt Tesseract (97.7% vs 87%)           |   |
|  |  [x] USE_DOCLING_FIRST    Docling statt Tika (97.9% tables)              |   |
|  |  [x] USE_WHISPERX         WhisperX mit Diarization                       |   |
|  |                                                                           |   |
|  |  Pipeline                                                                 |   |
|  |  [x] USE_PARSER_ROUTING   Benchmark-basierte Parser-Auswahl              |   |
|  |  [x] USE_FALLBACK_CHAIN   Fallback bei Parser-Fehler                     |   |
|  |  [x] USE_PII_DETECTION    GLiNER PII-Erkennung                           |   |
|  |                                                                           |   |
|  |  Storage                                                                  |   |
|  |  [x] USE_VECTOR_STORE     LanceDB Embedding-Speicher                     |   |
|  |  [x] USE_PRIORITY_QUEUES  Redis Streams Priority Queues                  |   |
|  |                                                                           |   |
|  +-----------------------------------------------------------------------+   |
|                                                                                   |
|  +---- WORKER SCALING -------------------------------------------------------+   |
|  |                                                                           |   |
|  |  Current Workers: 3                                                       |   |
|  |                                                                           |   |
|  |  Document Workers:  [2]  [+] [-]                                         |   |
|  |  Image Workers:     [1]  [+] [-]                                         |   |
|  |  Audio Workers:     [0]  [+] [-]                                         |   |
|  |                                                                           |   |
|  |  [Apply Changes]                                                         |   |
|  |                                                                           |   |
|  +-----------------------------------------------------------------------+   |
|                                                                                   |
|  +---- SERVICE ENDPOINTS ----------------------------------------------------+   |
|  |                                                                           |   |
|  |  Document Processor:  http://localhost:8005  [Test]                      |   |
|  |  Universal Router:    http://localhost:8030  [Test]                      |   |
|  |  Orchestrator:        http://localhost:8020  [Test]                      |   |
|  |  WhisperX:            http://localhost:9000  [Test]                      |   |
|  |  Meilisearch:         http://localhost:7700  [Test]                      |   |
|  |                                                                           |   |
|  +-----------------------------------------------------------------------+   |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 7. Mobile/Responsive View

```
+---------------------------+
| NEURAL VAULT       14:32 |
| [GPU] 48% VRAM           |
+---------------------------+
|                          |
| [=] Menu                 |
|                          |
+---------------------------+
|                          |
| +-- STATUS -------------+|
| |                       ||
| | Router     [online]   ||
| | Orchestr.  [online]   ||
| | DocProc    [online]   ||
| | Workers    3 active   ||
| |                       ||
| +-----------------------+|
|                          |
| +-- QUEUES -------------+|
| |                       ||
| | Priority   [##  ]  2  ||
| | Normal     [### ]  4  ||
| | Bulk       [####] 12  ||
| |                       ||
| | Total: 18 jobs        ||
| +-----------------------+|
|                          |
| +-- CURRENT JOB --------+|
| |                       ||
| | job-d4e5f6            ||
| | Scan_0042.jpg         ||
| | [====.]  processing   ||
| |                       ||
| +-----------------------+|
|                          |
+---------------------------+
| [Overview] [Jobs] [More] |
+---------------------------+
```

---

## 8. Farbschema

```
Hintergrund:     #0a0f14  (Dunkel)
Cards:           #111827  (Slate-900)
Borders:         #1f2937  (Slate-800)

Status Online:   #10b981  (Emerald-500)
Status Busy:     #f59e0b  (Amber-500)
Status Offline:  #ef4444  (Rose-500)
Status Idle:     #14b8a6  (Teal-500)

Accent Primary:  #14b8a6  (Teal-500)
Accent GPU:      #8b5cf6  (Violet-500)

Text Primary:    #e2e8f0  (Slate-200)
Text Secondary:  #94a3b8  (Slate-400)
Text Muted:      #64748b  (Slate-500)
```

---

## 9. Komponenten-Hierarchie

```
App
├── Header
│   ├── Logo + Title
│   ├── GPU Status Badge
│   └── System Time
│
├── Navigation Tabs
│   ├── Overview
│   ├── Pipeline
│   ├── Jobs
│   ├── Search
│   └── Settings
│
├── Tab Content
│   ├── OverviewTab
│   │   ├── ArchitectureDiagram
│   │   ├── QueueStatus
│   │   ├── ProcessorStatus
│   │   └── HealthChecks
│   │
│   ├── PipelineTab
│   │   ├── FileIntake
│   │   ├── DetectionStage
│   │   ├── RoutingStage
│   │   ├── ProcessingStage
│   │   └── EnrichmentStage
│   │
│   ├── JobsTab
│   │   ├── JobFilters
│   │   ├── JobTable
│   │   ├── JobDetails
│   │   └── Pagination
│   │
│   ├── SearchTab
│   │   ├── SearchInput
│   │   ├── SearchFilters
│   │   └── SearchResults
│   │
│   └── SettingsTab
│       ├── FeatureFlags
│       ├── WorkerScaling
│       └── ServiceEndpoints
│
└── Footer
    └── StatusBar + Logs
```

---

## 10. API Endpoints (Backend)

Die UI benötigt folgende API-Endpoints:

```typescript
// System Status
GET  /api/status/system          // Gesamtstatus
GET  /api/status/health          // Health aller Services
GET  /api/status/gpu             // GPU-Informationen

// Queues
GET  /api/queues                 // Queue-Statistiken
GET  /api/queues/:name           // Einzelne Queue
POST /api/queues/:name/clear     // Queue leeren

// Jobs
GET  /api/jobs                   // Job-Liste (paginiert)
GET  /api/jobs/:id               // Job-Details
POST /api/jobs                   // Job einreichen
POST /api/jobs/:id/retry         // Job wiederholen
DELETE /api/jobs/:id             // Job abbrechen

// Workers
GET  /api/workers                // Worker-Status
POST /api/workers/scale          // Worker skalieren

// Search
POST /api/search                 // Semantische Suche
GET  /api/search/similar/:id     // Ähnliche Dokumente

// Settings
GET  /api/settings/flags         // Feature Flags
PUT  /api/settings/flags         // Flags aktualisieren
GET  /api/settings/endpoints     // Service-Endpoints
POST /api/settings/endpoints/test // Endpoint testen
```
