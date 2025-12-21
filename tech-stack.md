# Tech Stack

## Core Infrastructure
| Component | Technology | Reason |
|:---|:---|:---|
| **Operating System** | Windows 11 | Primary user environment |
| **File System** | NTFS (D:, F:) | 7TB+ support, ACLs, timestamps |
| **Cloud Sync** | Nextcloud | Self-hosted, privacy-first |
| **Version Control** | Git | Migration rollback, audit trail |

## Automation & Scripting
| Component | Technology | Reason |
|:---|:---|:---|
| **Primary** | PowerShell 7+ | Native Windows, robust file ops |
| **Secondary** | Python 3.11+ | RAG pipelines, ML/AI integration |
| **OCR** | Tesseract / Docling | PDF/image text extraction |
| **Audio Transcription** | Whisper (local) | Video/audio metadata |

## AI & RAG Stack
| Component | Technology | Reason |
|:---|:---|:---|
| **Embedding Model** | sentence-transformers | Local, multilingual |
| **Vector Database** | ChromaDB / FAISS | Local persistence, good Python API |
| **RAG Framework** | LlamaIndex / LangChain | Flexible, well-documented |
| **Local LLM** | Ollama + Llama3 / Mistral | Privacy, no API costs |
| **Multimodal** | LLaVA / BakLLaVA | Image understanding |

## Naming Conventions
- **Files**: `YYYY-MM-DD_Category_Description.ext`
- **Folders**: `## Datenpool Name` (00-99 numbered)
- **Context**: `_context.md` in every significant folder

## Design Decisions
| Date | Decision | Rationale |
|:---|:---|:---|
| 2025-12-21 | Robocopy with `/COPY:DAT` | Avoid admin-only audit flags |
| 2025-12-21 | SHA256 for deduplication | Content-based, collision-resistant |
| 2025-12-21 | Git manifest on F: | Point-in-time rollback capability |
