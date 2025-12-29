# Docker & Stack Style Guide

## 1. Service Naming
*   Use functional, descriptive names (hyphen-separated).
*   **Bad**: `db`, `web`, `app`.
*   **Good**: `vector-store`, `rag-interface`, `llm-engine`.

## 2. Volume Management
*   **named volumes** for persistent data (DBs).
*   **bind mounts** for config files and the Data Pool (`F:\`).
*   **Strict Mapping**: Use clear relative paths `./config:/app/config`.

## 3. Network
*   Use a dedicated internal bridge network `ai-net`.
*   Do not expose ports to host unless necessary (e.g. only exposed via the Interface/Proxy).

## 4. Optimization (Raspberry Pi Specific)
*   **Restart Policy**: `restart: unless-stopped`.
*   **Logging**: Limit log size via `logging: driver: json-file`.
*   **Healtchecks**: Define healthchecks for critical services (`llm-engine`) so dependent services know when to start.
