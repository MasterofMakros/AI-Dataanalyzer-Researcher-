# Project Rules (CLAUDE.md)

## Operating Mode
- **Prime Directive:** Read `README.md`, `INITIAL.md` (if present), and `examples/` patterns before coding.
- **Planning:** No Code without a Plan. Use `generate-prp` to create a `PRP` (Product Requirements Prompt).
- **Validation:** No PR without passing Validation Gates (see below).

## Architecture & Code Organization
- **Microservices:** Docker-based. See `docker-compose.yml` for service definitions.
- **Frontend:** `ui/perplexica` (React/Next.js).
- **Backend:** `conductor-api`, `neural-search-api` (Python/FastAPI).
- **Scripts:** `scripts/` (PowerShell preferred for Windows host).
- **Docs:** `docs/agent/reference/` contains the source of truth for architecture.

## Coding Standards
- **Python:** Type hints required. Use partial validation (Pydantic).
- **PowerShell:** `Set-StrictMode -Version Latest`, `$ErrorActionPreference = "Stop"`.
- **Frontend:** TypeScript strict mode.
- **Logging:** Structured logging where possible. No `print()` in production code.

## Testing & Validation Gates
The following must pass before any `execute-prp` is considered "Done":
1.  **Docker Config:** `docker compose config --quiet` (Must match existing `docker-compose.yml`).
2.  **Validation Script:** `./scripts/validate.ps1` (covers healthchecks and basic tests).
3.  **Dependency Check:** IDEs must resolve imports (e.g., `npm install` in `ui/perplexica`).

## Documentation
- **PRPs:** Every feature gets a PRP in `PRPs/<slug>.md`.
- **Reference:** Update `docs/agent/reference/` if you add new services or ports.
- **Examples:** Add new patterns to `examples/` if you solve a novel problem.
