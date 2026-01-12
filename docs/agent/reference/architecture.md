# Architecture Reference

## Core Pattern
This project follows a **Microservices Architecture** orchestrated by Docker Compose.

**Key Principles:**
1.  **Local-First:** All processing happens on the host machine.
2.  **API-Driven:** Services communicate via REST APIs (Conductor API, Neural Search API).
3.  **Queue-Based:** Heavy lifting (OCR, Transcription) is offloaded to Workers via Redis Queues.
4.  **RAG-Centric:** Information is retrieved from Qdrant and synthesized by Ollama.

## Diagram (Abstract)
`Frontend (Perplexica)` -> `Neural Search API` -> `Qdrant` + `Ollama`
`Ingestion` -> `Universal Router` -> `Redis` -> `Workers` -> `Conductor API` -> `Qdrant`

For the full visual diagram, see `README.md`.
