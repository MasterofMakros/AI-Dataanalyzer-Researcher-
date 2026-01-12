# CLAUDE.md — Conductor Project Rules

## Purpose
You are an AI coding agent working in the Conductor repository. Your job is to implement changes safely, reproducibly, and with complete validation.

## Non-negotiables (MUST)
- MUST create a plan before editing code for non-trivial changes.
- MUST keep changes small and reviewable (atomic commits).
- MUST run validation gates after changes (see below).
- MUST update docs when behavior, ports, commands, or setup changes.

## Repo Map (high-signal)
- `ui/perplexica/` — React/TS UI (Neural Search)
- `docker-compose.yml` — deployment profiles (base/gpu/intelligence)
- `scripts/` — validation & helper scripts (`validate.ps1`, `doctor.ps1`)
- `tests/` — test suite (pytest)
- `docs/` — architecture + ADRs

## Coding Conventions
- Prefer explicit names over cleverness.
- Avoid hidden side effects in modules that run at import-time.
- Log at boundaries (ingest → process → index → search).

## Validation Gates (MUST PASS)
1) Repo health:
   - `powershell ./scripts/doctor.ps1`
2) Python:
   - `python -m compileall .`
   - `pytest -q` (or documented alternative if tests require compose)
3) Docker:
   - `docker compose config -q`
   - `docker compose up -d` (base) -> Check Key Endpoints
4) UI (if touched):
   - (run from `ui/perplexica/`) `npm install` + `npm run build`

## Documentation Rules
- If a port/service name/URL changes: update README table + quickstart.
- If setup changes: update `.env.example` and/or scripts.
