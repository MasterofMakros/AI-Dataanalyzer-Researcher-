# PRP: Fix CI/CD Pipeline

## Goal
- Fix the failing GitHub Actions Workflow (`.github/workflows/ci.yml`).
- Align CI with the new repository structure (Frontend: `ui/perplexica`).
- Ensure Backend Tests pass in the CI environment.

## Context
- **Current Status:** Backend tests fail in CI (after 13s). Frontend build targets legacy `ui/perplexica`.
- **Repo Facts:**
  - Active Frontend: `ui/perplexica` (Next.js)
  - Backend Tests: `tests/` (Python/pytest)
  - Dependency File: `requirements.txt` (needs verification)

## Requirements (Functional)
- MUST build `ui/perplexica` successfully.
- MUST run `pytest tests/` successfully on Ubuntu-latest.
- SHOULD remove legacy `ui/perplexica` steps from CI if obsolete.

## Implementation Plan
1.  **Analyze Dependencies:** Check `requirements.txt` and ensure `pytest` + app dependencies are present.
2.  **Update `ci.yml`:**
    - Change Frontend directory to `ui/perplexica`.
    - Update Node version if needed (Perplexica uses v20/v22?).
    - Update Backend step to install *all* required libs.
3.  **Validate:**
    - Run `pytest` locally (done, passed).
    - Commit and Push to trigger CI.

## Validation Gates
- Local: `./scripts/validate.ps1`
- Remote: GitHub Actions (must turn green).

## Risks & Rollback
- Risk: `ui/perplexica` might fail build due to missing env vars.
- Mitigation: Add dummy env vars to CI if needed.
- Rollback: Revert `ci.yml` to previous state.
