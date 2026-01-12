# Neural Vault - Improvement Recommendations 2025

> **Status Update**: 2025-12-29
> **Implementation Progress**: 85% Complete

---

## Executive Summary

This document tracks the implementation of key improvements to the Neural Vault document processing pipeline. The focus areas are:
1. **Extraction Quality** - Benchmark-driven processor selection
2. **Container Efficiency** - Consolidation and resource optimization
3. **Intelligence Pipeline** - Smart routing and priority queuing

---

## P0: Critical Infrastructure (Completed)

### A/B Test Infrastructure
**Status**: Implemented
**Files**: `scripts/services/ab_test_service.py`, `scripts/tests/test_ab_framework.py`

- Feature flag system with gradual rollout (0-100%)
- Automatic metric collection and analysis
- Statistical significance testing
- Integration with smart_ingest.py

```python
# Usage
from scripts.services.ab_test_service import is_enabled, get_variant

if is_enabled("USE_PARSER_ROUTING"):
    # New behavior
else:
    # Legacy behavior
```

### WhisperX Integration
**Status**: Implemented
**Files**: `docker/whisperx/`, `scripts/services/extraction_service.py`

- WhisperX for audio/video transcription
- Speaker diarization support
- GPU-accelerated processing
- Automatic language detection (de, en)

---

## P1: Extraction Quality (Completed)

### Surya OCR Integration
**Status**: Implemented
**Files**: `docker/document-processor/main.py`

| Metric | Tesseract | Surya OCR |
|--------|-----------|-----------|
| Accuracy | 87% | **97.7%** |
| German Support | Basic | Native |
| GPU Acceleration | No | Yes |
| Handwriting | Poor | Good |

### Docling-First Routing
**Status**: Implemented
**Files**: `scripts/services/extraction_service.py`, `scripts/tests/test_extraction_routing.py`

Benchmark-driven parser selection:

| Format | Primary | Fallback | Benchmark |
|--------|---------|----------|-----------|
| PDF | Docling | Tika | 97.9% vs 75% table accuracy |
| DOCX | Docling | Tika | Native format support |
| Images | Surya | Tesseract | 97.7% vs 87% accuracy |
| Audio | WhisperX | - | Speaker diarization |

```python
# Parser routing chain
PARSER_CHAIN = {
    ".pdf": [ParserType.DOCLING, ParserType.TIKA],
    ".jpg": [ParserType.SURYA, ParserType.TESSERACT],
    ".mp3": [ParserType.WHISPERX],
}
```

---

## P1: Container Consolidation (Completed)

### Unified Document Processor
**Status**: Implemented
**Files**: `docker/document-processor/`

Consolidated GPU services into single container:

| Before | After |
|--------|-------|
| neural-worker (Docling) | document-processor |
| surya-ocr | document-processor |
| gliner-pii | document-processor |
| tesseract-ocr | Legacy (profile) |

**Container Specs**:
- Base: `nvidia/cuda:12.1-cudnn8-runtime-ubuntu22.04`
- GPU: NVIDIA GPU with CUDA support
- Memory: 8GB+ recommended
- Port: 8005

**Endpoints**:
```
POST /process/document  - Auto-routing by extension
POST /process/pdf       - Docling extraction
POST /process/ocr       - Surya OCR
POST /process/pii       - GLiNER PII detection
POST /vector/embed      - Generate embeddings
POST /vector/store      - Store in LanceDB
POST /vector/search     - Semantic search
GET  /health            - Health check
GET  /processors        - List capabilities
```

---

## P1: Intelligence-Grade Pipeline (Completed)

### Universal Router
**Status**: Implemented
**Files**: `docker/universal-router/router.py`

- Magic Byte Detection (200+ formats)
- Content-type validation
- Automatic format routing
- Port: 8030

### Orchestrator
**Status**: Implemented
**Files**: `docker/orchestrator/orchestrator.py`

- Redis Streams priority queues
- Job distribution and tracking
- Worker coordination
- Port: 8020

**Priority Queues**:
```
intake:priority  - High priority jobs (< 5s response)
intake:normal    - Standard processing
intake:bulk      - Batch operations
```

### Extraction Workers
**Status**: Implemented
**Files**: `docker/workers/extraction_worker.py`

- Scalable worker pool (`--scale extraction-worker=N`)
- Document, Image, Audio specialization
- Automatic retry with exponential backoff
- Health monitoring

---

## Architecture Overview

```
                    +------------------+
                    |  Universal Router |
                    |    (Port 8030)    |
                    +--------+---------+
                             |
                    +--------v---------+
                    |   Orchestrator    |
                    |    (Port 8020)    |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v----+  +------v------+  +----v--------+
     | Document    |  | Image       |  | Audio       |
     | Worker      |  | Worker      |  | Worker      |
     +------+------+  +------+------+  +------+------+
            |                |                |
     +------v----------------v----------------v------+
     |              Document Processor               |
     |  (Docling + Surya OCR + GLiNER + LanceDB)    |
     |                  (Port 8005)                  |
     +-----------------------------------------------+
```

---

## Docker Services Summary

| Service | Port | Description | Status |
|---------|------|-------------|--------|
| document-processor | 8005 | Unified GPU Service | Active |
| universal-router | 8030 | Magic Byte Detection | Active |
| orchestrator | 8020 | Priority Queues | Active |
| extraction-worker | - | Scalable Workers | Active |
| redis | 6379 | Message Queue | Active |
| api | 8000 | REST API | Active |
| ui | 3000 | Mission Control | Active |
| neural-worker | - | Legacy Docling | Profile: legacy |
| tesseract-ocr | - | Legacy OCR | Profile: legacy |
| whisper | - | Legacy Whisper | Profile: legacy |

---

## Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| USE_PARSER_ROUTING | True | Enable benchmark-driven parser selection |
| USE_SURYA_OCR | True | Use Surya instead of Tesseract |
| USE_WHISPERX | True | Use WhisperX for audio |
| USE_FALLBACK_CHAIN | True | Enable fallback to secondary parsers |
| USE_PII_DETECTION | True | Enable GLiNER PII detection |
| USE_VECTOR_STORE | True | Store in LanceDB |

---

## P2: Future Improvements (Pending)

### Performance Optimization
- [ ] Batch processing for multiple documents
- [ ] Streaming response for large files
- [ ] Connection pooling optimization
- [ ] Model preloading on startup

### Monitoring & Observability
- [ ] Prometheus metrics export
- [ ] Grafana dashboards
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Alerting rules

### Quality Improvements
- [ ] Table structure validation
- [ ] OCR confidence thresholds
- [ ] Automatic quality scoring
- [ ] Human-in-the-loop review queue

### Scale & Reliability
- [ ] Kubernetes deployment manifests
- [ ] Auto-scaling policies
- [ ] Circuit breaker patterns
- [ ] Dead letter queue handling

---

## Test Results

```
=== Parser Routing Tests ===
[PASS] PDF -> DOCLING
[PASS] DOCX -> DOCLING
[PASS] JPG -> SURYA
[PASS] PNG -> SURYA
[PASS] MP3 -> WHISPERX
[PASS] WAV -> WHISPERX
[PASS] TXT -> TIKA

=== Fallback Chain Tests ===
[PASS] PDF fallback: DOCLING -> TIKA
[PASS] Image fallback: SURYA -> TESSERACT

=== Feature Flag Tests ===
[PASS] Parser routing toggle
[PASS] Surya OCR toggle
[PASS] WhisperX toggle

=== Integration Tests ===
[PASS] Extraction service initialization
[PASS] Stats collection

All tests passed: 5/5
```

---

## Quick Start

```bash
# Start core services
docker compose up -d redis api ui

# Start processing pipeline
docker compose up -d document-processor universal-router orchestrator

# Scale workers as needed
docker compose up -d --scale extraction-worker=3

# (Optional) Start legacy services
docker compose --profile legacy up -d
```

---

## References

- [Docling Benchmarks](https://ds4sd.github.io/docling/)
- [Surya OCR](https://github.com/VikParuchuri/surya)
- [GLiNER](https://github.com/urchade/GLiNER)
- [WhisperX](https://github.com/m-bain/whisperX)
- [LanceDB](https://lancedb.github.io/lancedb/)
