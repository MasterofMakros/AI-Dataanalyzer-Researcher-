# Implementation Plan - Compose Overlay Fixes (special-parser)

**Status:** Done
**Date:** 2026-01-14
**Context:** Fix special-parser references and enable overlay validation.

## 1. Goal & Context
*   **What:** Remove special-parser references from base compose, align intelligence overlay, update docs, and validate configs.
*   **Why:** Base stack must be self-contained; overlay should validate cleanly.
*   **User Story:** As a maintainer, I want to run the core stack and optional intelligence overlay without compose errors.

## 2. Architecture & Design
*   **Components:** `docker-compose.yml`, `docker-compose.intelligence.yml`, `README.md`, `docs/architecture/service-matrix.md`, `AGENTS.md`
*   **Data Models:** None.
*   **Dependencies:** None.

## 3. Implementation Steps (Execution)
- [x] Remove special-parser workers from base compose.
- [x] Fix intelligence compose conflicts (replicas + container_name, ffmpeg/tesseract container name collision).
- [x] Update README quickstart and agent guidance.

## 4. Verification Plan (Validate)
**Automated Tests:**
*   [x] Run `docker compose config -q`
*   [x] Run `docker compose -f docker-compose.yml -f docker-compose.intelligence.yml config -q`
*   [x] Run `./scripts/validate.sh --quick`

**Manual Verification:**
*   [ ] Start core stack and overlay (deferred).

## 5. Execution Notes
*   Attempted `docker compose --profile gpu up -d` -> failed: Docker daemon not running.
*   Full smoke/validate for core + overlay deferred until Docker Desktop is running.

## 6. Rollback Strategy
*   Revert compose/doc changes to restore prior behavior.
