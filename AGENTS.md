# AGENTS.md - Working Agreement for AI Coding Agents (Codex-first)

## Purpose
This repository is maintained with an agent-first workflow. Your job is to implement changes safely, reproducibly, and with evidence.

## Read First (in this order)
1) README.md
2) CLAUDE.md (project rules, non-negotiables, validation gates)
3) docs/index.md (documentation table of contents)
4) docs/PROJECT_STATUS.md (single source of truth for planned/in-progress/done)
5) PRPs/ (feature blueprints; each planned feature must have one PRP)
6) scripts/validate.* and scripts/smoke.* (required gates)

## The Workflow (PIV Loop, tool-agnostic)
### PRIME (read-only)
- Understand current behavior by reading docs and inspecting repo structure.
- Identify impacted components, configuration, and existing patterns.
- Output a short "Prime Snapshot" (risks + files likely to change).
- Do NOT change code during PRIME.

### PLAN (PRP-first)
- Ensure there is a PRP for the feature in PRPs/.
- PRP must include: Goal/Non-Goals, ordered plan, Acceptance Criteria, Validation commands, Rollback.
- Do NOT implement until the PRP is complete.

### EXECUTE (small, deterministic changes)
- Implement strictly following the PRP plan.
- Keep commits small and reviewable.
- Update docs when behavior/config/ports/services change.

### VALIDATE (hard gate)
- Run scripts/validate.* and scripts/smoke.* (if present).
- Run docker compose config -q.
- Fix until everything is green.

### REPORT (evidence + status)
- Update docs/PROJECT_STATUS.md with status and evidence (commit/PR + validation results).
- Write a short execution report (what changed, what ran, what remains).

## Non-negotiables
- No breaking changes without explicit migration + doc update.
- No port changes without updating README + docs/architecture/service-matrix.md.
- No references to removed components (e.g., Mission Control) outside docs/_archive.
- Runtime data must not be committed (respect .gitignore; keep data/ and var/ clean).

## Standard Commands (choose your OS)
### Windows (PowerShell)
- .\\scripts\\validate.ps1
- .\\scripts\\smoke.ps1 (if present)
- docker compose config -q
- docker compose up -d

### Linux/macOS (bash)
- ./scripts/validate.sh
- ./scripts/smoke.sh (if present)
- docker compose config -q
- docker compose up -d
