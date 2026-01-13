# Milvus-Adaptionsplan: Backlog, Benchmarks, Index-Presets & Hybrid-API

Dieses Dokument liefert eine konkretisierte Aufgabenliste (Ticket-Backlog), Mess-Harness, Benchmarks/A-B-Setup sowie eine Index-Preset-Matrix pro Datendomäne für das Conductor/Neural-Vault-Setup.

## 1) Ticket-Backlog (konkret + priorisiert)

> Schätzungsskala: S (1-3 Tage), M (4-8 Tage), L (2-4 Wochen)

### EPIC A — Mess-Harness & Baseline
- **A1**: Query-Gold-Set definieren (200 Queries je Modalität: Text/Audio/Video) inkl. Labels (relevant/irrelevant). **S**
- **A2**: Benchmark-Schema (JSONL) und Loader implementieren. **S**
- **A3**: Harness für p50/p95, Recall@K, MRR/NDCG, QPS, RAM-Footprint. **M**
- **A4**: Baseline-Run dokumentieren und speichern. **S**

### EPIC B — Hybrid Search + RRF
- **B1**: Hybrid-Search-API in Conductor-API (Dense + Sparse) skizzieren/implementieren. **M**
- **B2**: RRF/Weighted-Fusion implementieren + Parameterkonfiguration. **M**
- **B3**: Query-Router (keyword-dominant vs. semantic). **M**
- **B4**: A/B-Tests (Dense-only vs. Hybrid). **M**

### EPIC C — Index-Profiling je Datendomäne
- **C1**: Index-Preset-Matrix finalisieren (Text/Audio/Video/Archive). **S**
- **C2**: Parameter-Sweeps (HNSW/IVF/PQ) je Collection durchführen. **M**
- **C3**: Recall@K vs. RAM vs. p95-Latenz vergleichen. **M**

### EPIC D — Read-Scaling / Query Replicas
- **D1**: Search-Worker-Pool + Routing definieren. **M**
- **D2**: Cache-Layer (Top-K / Hot Queries). **M**
- **D3**: Load-Tests mit parallelem Ingest. **M**

### EPIC E — Scalar/Metadata-Indexing
- **E1**: Standard-Filterfelder (Zeit, Typ, Kategorie) definieren. **S**
- **E2**: Index-Strategien pro Filterfeld implementieren. **M**
- **E3**: Filter-Heavy Benchmarks. **S**

### EPIC F — Storage-Tiering (Hot/Cold)
- **F1**: Hot/Cold-Policy + Warmup definieren. **M**
- **F2**: Cold/Hot Latency Benchmarks. **M**

### EPIC G — Observability
- **G1**: Metrics-Export (Search/Ingest/Queue Depth). **M**
- **G2**: Grafana-Dashboard für p95/QPS/Queue-Lags. **M**

## 2) Mess-Harness-Skripte + Benchmark-Daten

### 2.1 Ordnerstruktur
```
/docs/benchmarks/
  milvus_adaptation_plan.md
  query_set_template.jsonl
/scripts/benchmarks/
  run_benchmark.py
/data/benchmarks/
  README.md
```

### 2.2 Query-Set JSONL (Template)
**Format:**
```json
{"id":"text-001","modality":"text","query":"Rechnung 2024 MWST","expected_ids":["doc_123"],"notes":"Keyword-heavy"}
```

### 2.3 Harness-Funktionen (Ziele)
- **Latency**: p50/p95/p99 pro Query-Typ
- **Quality**: Recall@K, MRR@K, NDCG@K
- **Throughput**: QPS unter Last
- **Memory**: RSS/Index-Size (pro 1M Vektoren)

### 2.4 A/B-Setup (Dense-only vs. Hybrid)
- **Group A**: Qdrant Dense Search
- **Group B**: Hybrid Search (Dense + Sparse + RRF)
- **Vergleich**: MRR/NDCG@10 + Zero-Result-Rate

## 3) Index-Profil-Matrix (pro Datendomäne)

| Datendomäne | Charakteristik | Preset | Ziel | Erwarteter Effekt |
|---|---|---|---|---|
| Text/Docs (Hot) | kurze Queries, hohe Interaktivität | HNSW (hohe recall, niedrige Latenz) | p95 < 300ms | Latenz ↓, Recall ↑ |
| Text/Archive (Cold) | große Collections, seltene Zugriffe | IVF-PQ + Quantization | RAM ↓ 30-60% | Speicher ↓, p95 stabil |
| Audio-Transkripte | lange Dokumente + Keyword Queries | Hybrid (Dense + Sparse) | Recall@10 ↑ | Quality ↑ |
| Video/Multimodal | hohe Datenmenge | IVF-PQ + Tiering | RAM ↓ | Scale ↑ |

## 4) Index-Preset-Matrix (Parameter-Skizze)

> Placeholder: wird nach ersten Benchmarks finalisiert

**HNSW (Hot Text)**
- M: 32
- efConstruction: 128
- efSearch: 64

**IVF-PQ (Archive)**
- nlist: 4096
- m: 16
- nbits: 8

**Quantization (Large Scale)**
- type: scalar/pq
- rescore: enabled

## 5) Hybrid-Search-API (Skizze)

### 5.1 Endpoint
`POST /search/hybrid`

### 5.2 Request
```json
{
  "query": "Rechnung 2024 MWST",
  "limit": 10,
  "filters": {
    "doc_type": "invoice",
    "year": 2024
  },
  "routing": "auto",
  "weights": {
    "dense": 0.6,
    "sparse": 0.4
  }
}
```

### 5.3 Response
```json
{
  "results": [
    {
      "id": "doc_123",
      "score": 0.91,
      "source": "dense+sparse",
      "highlights": ["MWST", "2024"],
      "metadata": {
        "filename": "Rechnung_2024.pdf"
      }
    }
  ],
  "metrics": {
    "dense_latency_ms": 120,
    "sparse_latency_ms": 80,
    "fusion_latency_ms": 10
  }
}
```

## 6) Konkrete Benchmarks (A/B)

| Benchmark | A (Dense-only) | B (Hybrid) | Ziel |
|---|---|---|---|
| MRR@10 | Baseline | +10–30% | +10–30% |
| NDCG@10 | Baseline | +5–20% | +10% |
| Zero-Result-Rate | Baseline | -30–60% | -40% |
| p95 Latency | Baseline | +/- 10% | <= 500ms |
| RAM / 1M vectors | Baseline | -30–60% | -40% |

