# Product: Neural Vault (formerly AI-Ready Data Pool)

## Vision
Transform a **10TB+** unstructured data lake into an automated, privacy-first **"Internal Google"**. The system, dubbed "Neural Vault", uses local AI to autonomously ingest, classify, deduplicate, and index all digital life assets (Documents, Photos, Videos, Audio) for instant retrieval and semantic interaction.

## Users
1.  **Primary User**: Owner (Business + Private data management)
2.  **The "Guardian"**: Local Agents (n8n, Ollama, Watchers) that organize data 24/7.
3.  **Family Members**: Read-Only access to specific pools (e.g., Photos, Recipes) via Nextcloud/Immich.

## Goals
1.  **Instant Omniscient Search**: Find any fact, scene in a video, or invoice content in <3 seconds.
2.  **Privacy First (Local Only)**: No data leaves the LAN. All AI (OCR, Transcribe, Embedding) runs on local Ryzen AI hardware.
3.  **Zero-Touch Organization**: Files classify themselves upon arrival (`_Inbox` -> `Target Folder`).
4.  **10TB Scalability**: Architecture designed for high-throughput ingestion and massive vector indices.
5.  **Deduplication**: SHA-256 for exact matches, Perceptual Hashing for visual near-duplicates.

## High-Level Features
- [x] Data Pool Taxonomy (Johnny.Decimal style)
- [x] Semantic `_context.md` files
- [x] Simulation of Smart Ingestion (n8n + Mock AI)
- [ ] **Hardware Upgrade**: Migration to Ryzen AI 9 HX 370
- [ ] **Smart Ingestion Pipeline**: n8n workflows for auto-sorting
- [ ] **Visual Intelligence**: Immich deployment for photo/video analysis
- [ ] **Semantic Core**: Qdrant Vector Database integration
