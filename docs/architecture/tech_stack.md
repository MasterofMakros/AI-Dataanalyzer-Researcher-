# Tech Stack: Neural Vault Edition (V2.0)

*Stand: 2025-12-26*

---

## Core Infrastructure (The Power Plant)

| Component | Technology | Reason |
|:---|:---|:---|
| **Compute Core** | **AMD Ryzen AI 9 HX 370** | High-perf NPU for local AI, energy efficient |
| **Storage Node** | Raspberry Pi 4 | Legacy witness, IoT gateway |
| **Storage (Cold)** | 18TB HDD (NTFS/ZFS) | Mass storage for 10TB+ data |
| **Storage (Hot)** | 4TB NVMe | Vector Index, Thumbnails, Database |
| **Network** | Cloudflare Tunnel + Tailscale | Secure public/private access |

---

## Application Layer

| Component | Technology | Reason | ADR |
|:---|:---|:---|:---|
| **Orchestrator** | **n8n** | Visual workflow automation, "Central Nervous System" | - |
| **File System** | **Nextcloud** | Web/Mobile/Desktop access, External Storage für F:/ | [ADR-006](docs/ADR/ADR-006-nextcloud-integration.md) |
| **Photos/Video** | **Immich** | Google Photos alternative, local face/object recognition | - |
| **Vector DB** | **Qdrant** | 10-30ms Latency, Hybrid Search, Rust-basiert | [ADR-001](docs/ADR/ADR-001-vector-database.md) |
| **Ledger** | **SQLite** | "Shadow Ledger" für Datei-Tracking & Original-Namen | [ADR-006](docs/ADR/ADR-006-nextcloud-integration.md) |

---

## AI & Intelligence Stack

| Component | Technology | Performance | ADR |
|:---|:---|:---|:---|
| **LLM Inference** | **Ollama** (Llama3, Mistral) | Lokale Kategorisierung & Reasoning | - |
| **Vision** | **CLIP / LLaVA** | Image Tagging, Beschreibungen | - |
| **Audio** | **Faster-Whisper** | Video/Voice Note Transkription | - |
| **OCR (Print)** | **Surya OCR** | **97.7% Accuracy** auf Rechnungen | [ADR-005](docs/ADR/ADR-005-ocr-strategy.md) |
| **OCR (Handwriting)** | **TrOCR** (Microsoft) | **96% Accuracy**, Transformer-based | [ADR-005](docs/ADR/ADR-005-ocr-strategy.md) |
| **Document Parser** | **IBM Docling** | **97.9% Table Accuracy**, native Office Parsing | [ADR-004](docs/ADR/ADR-004-document-etl.md) |
| **RAG Framework** | **LlamaIndex** | 35% Retrieval Boost vs. LangChain | [ADR-004](docs/ADR/ADR-004-document-etl.md) |

---

## Processing Pipeline (Tiered)

| Tier | Tool | Funktion | Wann |
|:---|:---|:---|:---|
| **Tier 0** | **scandir_rs** | Dateisystem-Scan (2-17x schneller) | Initial-Indexierung |
| **Tier 1** | **Apache Tika** | Dateityp + Quick Text (1400+ Formate) | Jede Datei |
| **Tier 2** | **IBM Docling** | Deep Parse (Tabellen, Formeln) | Komplexe Dokumente |
| **Tier 3** | **Surya OCR** | OCR für Scans | Gescannte PDFs |
| **Tier 4** | **TrOCR** | Handschrift-OCR | Notizen, Whiteboards |
| **Tier 5** | **Ollama** | KI-Klassifizierung | Alle Dateien |

---

## Specialist Tools (Green IT / Efficiency)

| Component | Technology | Efficiency Advantage |
|:---|:---|:---|
| **Tier-1 Parser** | **Apache Tika** (Java/Docker) | **Universal**: 1400+ formats, ~300MB |
| **Archive Access** | **Ratarmount** (Python/FUSE) | **Zero-Copy**: Mounts RARs ohne Extraktion |
| **Video Dedup** | **Czkawka** (Rust) | **High-Perf**: Memory-safe, schneller Hash |
| **Video Transcode** | **FFmpeg w/ VCN** | **Hardware Accel**: Ryzen ASICs statt CPU |
| **File Scanner** | **scandir_rs** (Rust/Python) | **2-17x faster**: Parallel I/O |

---

## Qualitätssicherung

| Component | Technology | Funktion | ADR |
|:---|:---|:---|:---|
| **Quality Gates** | Python (n8n Code Node) | 6 automatische Prüfungen | [ADR-007](docs/ADR/ADR-007-file-processing-quality.md) |
| **Quarantine** | Filesystem + SQLite | Fehlerhafte Dateien isolieren | [ADR-007](docs/ADR/ADR-007-file-processing-quality.md) |
| **RAG Evaluation** | RAGAS / Arize Phoenix | Faithfulness, Groundedness | [UAT_PLAN.md](docs/UAT_PLAN.md) |

---

## Naming & Organization

### Smart Rename Format
```
YYYY-MM-DD_Category_Entity_Description.ext
```

**Beispiele:**
- `2024-05-12_Rechnung_Bauhaus_Gartenmaterial.pdf`
- `2024-12-26_Kontoauszug_Sparkasse_November.pdf`
- `2024-08-15_Foto_Urlaub_Barcelona.jpg`

### Duplicate Protection

| Typ | Methode | Aktion |
|:---|:---|:---|
| **Exakt** | SHA-256 Hash | Auto-Move to `_duplicates/` |
| **Visuell** | Perceptual Hash (pHash) | Gruppieren, manuelles Review |
| **Semantisch** | Vektor-Ähnlichkeit >95% | Als "Related" verlinken |

---

## Zwei-Zonen-Modell

| Zone | Pfad | Verarbeitung |
|:---|:---|:---|
| **🟢 Active** | `F:/_Inbox/` | Analyse → Rename → Move → Index |
| **🔵 Passive** | `F:/*` (Rest) | Nur Indexierung (keine Änderung) |

*Details: [ADR-006](docs/ADR/ADR-006-nextcloud-integration.md)*

---

## Docker-Container

| Container | Image | Ports |
|:---|:---|:---|
| `nextcloud` | nextcloud:28-apache | 8080 |
| `nextcloud-db` | mariadb:10.11 | 3306 (intern) |
| `n8n` | n8nio/n8n | 5678 |
| `qdrant` | qdrant/qdrant | 6333, 6334 |
| `ollama` | ollama/ollama | 11434 |
| `tika` | apache/tika | 9998 |

---

*Letzte Aktualisierung: 2025-12-26*
