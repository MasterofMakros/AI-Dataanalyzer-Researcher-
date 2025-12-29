# Agent Context - Conductor Project

## Quick Reference

**Repository:** https://github.com/MasterofMakros/AI-Dataanalyzer-Researcher-
**Branch:** main
**Working Directory:** F:\conductor

## Git Workflow

Nach JEDER Aenderung diese Befehle ausfuehren:

```bash
cd F:\conductor
git add -A
git commit -m "beschreibung der aenderung"
git push origin main
```

## Projekt-Struktur

- `docker/` - Docker Container Definitionen
- `mission_control_v2/` - React Frontend (Neural Search UI)
- `scripts/` - Python Scripts und Utilities
- `docs/` - Dokumentation und ADRs
- `config/` - Konfigurationsdateien

## Aktuelle Services

| Service | Port | Zweck |
|---------|------|-------|
| mission-control | 3000 | Web UI |
| conductor-api | 8000 | REST API |
| neural-search-api | 8040 | RAG/LLM |
| meilisearch | 7700 | Volltext |
| qdrant | 6333 | Vektoren |
| ollama | 11434 | LLM |

## Konventionen

- Commits: Conventional Commits (feat:, fix:, docs:, chore:)
- Deutsch fuer Dokumentation, Englisch fuer Code
- Keine Secrets in Git (.env ist in .gitignore)

## Starten des Projekts

```bash
cd F:\conductor
docker compose up -d
```

## Letzte Aenderungen

- 2025-12-29: GitHub Standards hinzugefuegt
- 2025-12-29: Projekt-Bereinigung
- 2025-12-29: Neural Search API implementiert
