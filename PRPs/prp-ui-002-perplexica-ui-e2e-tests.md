# PRP-UI-002: Perplexica UI E2E Tests (Playwright) - Critical User Flows + Error States

## Status
- State: planned
- Owner: codex
- Last Updated: 2026-01-14

## Purpose
Add a deterministic UI end-to-end test suite for the modified Perplexica UI to catch regressions and ensure feature completeness (search, sources, preview, modes, error handling).

## Background / Problem
Current smoke tests only verify the UI endpoint returns HTTP 200. This does not validate:
- search results render correctly,
- sources list and metadata/icons behave correctly,
- media previews work (image/audio/video),
- "optimization modes" (if present) behave correctly,
- UI handles backend outages gracefully.

We need a repeatable Playwright suite that can run locally and in CI.

## Scope (Goals)
1) Add Playwright E2E tests for the top user journeys:
   - load UI
   - perform search query
   - see results + sources
   - open source details (if present)
   - validate format icons are displayed for at least one known source
   - open media preview for:
     - image
     - audio
     - video
   - switch "optimization mode" (if present) and assert visible change
2) Add "error state" tests:
   - Search API down -> UI shows clear error/empty state (not a crash/spinner forever).
3) Stabilize selectors:
   - add `data-testid` attributes to key UI elements (minimal, non-invasive).
4) Provide runner commands:
   - `npm run test:e2e` (headless by default)
   - optional `npm run test:e2e:ui` (headed/debug)
5) Integrate with `scripts/validate.*` optionally via `--ui-e2e`.

## Non-Goals
- Full visual regression testing (pixel diffs).
- Testing every minor UI edge case.
- Performance benchmarking.

## Repository Additions / File Layout
Assuming UI lives under `ui/perplexica` (adjust if moved):
- `ui/perplexica/playwright.config.*`
- `ui/perplexica/tests/e2e/*.spec.*`
- `ui/perplexica/package.json` scripts:
  - `test:e2e`
  - `test:e2e:ui`
- `docs/dev/ui-e2e-testing.md`

## Test Data Strategy (Deterministic)
E2E UI tests need deterministic content. Two valid options:

A) Preferred: use the E2E harness from PRP-FMT-001 to ingest samples before UI tests.
- UI tests then search for a known token (`E2E_TOKEN_DOCX`, etc.).

B) Fallback: mock/stub the Search API responses (only for UI rendering tests).
- Use this only for isolated UI behavior, not end-to-end integration.

This PRP expects option A for at least 1 "real E2E" spec.

## Assumptions / Constraints
- UI base URL defaults to `http://localhost:3100`.
- Allow override via `E2E_UI_BASE_URL` environment variable.

## Implementation Plan (Ordered)
1) Add Playwright dependencies in UI project:
   - install Playwright
   - add scripts in `package.json`
2) Add stable selectors (`data-testid`) to the UI:
   Required testids (minimum):
   - `search-input`
   - `search-submit`
   - `results-list`
   - `result-item`
   - `sources-panel` (or equivalent)
   - `source-item`
   - `format-icon`
   - `media-preview-open`
   - `media-preview-player` (img/audio/video container)
   - `optimization-mode-toggle` (if exists)
   - `error-banner` (for error state)
3) Implement E2E specs:
   - `ui_loads.spec`: homepage loads, no console fatal errors
   - `search_returns_results.spec`: perform query for a known E2E token; assert results and sources
   - `sources_and_icons.spec`: assert at least one source has a format icon
   - `media_preview_image.spec`: open image preview; assert image element visible
   - `media_preview_audio.spec`: open audio preview; assert audio element visible
   - `media_preview_video.spec`: open video preview; assert video element visible
   - `optimization_mode.spec` (conditional): toggle mode; assert UI indicates mode changed
   - `error_state_backend_down.spec`: simulate Search API down:
     - method 1: stop container for Search API in test setup (preferred for real integration)
     - method 2: route interception returning 502 (fallback)
4) Provide a CI-friendly mode:
   - headless
   - retries = 1-2
   - traces/screenshots on failure
   - no brittle CSS selectors (prefer `data-testid`)
   - wait for explicit "results loaded" testid before assertions
5) Add documentation:
   - prerequisites: stack running
   - recommended workflow: run format harness first, then UI E2E
6) Optional integration into `scripts/validate.*`:
   - add `--ui-e2e` flag to execute Playwright tests

## Acceptance Criteria (Testable)
- [ ] `npm run test:e2e` passes locally when stack is running.
- [ ] At least one spec uses real backend data (E2E tokens) rather than mocks.
- [ ] Tests use `data-testid` selectors (no brittle CSS selectors).
- [ ] Error-state test proves UI does not hang or crash when backend is unavailable.
- [ ] On failure, Playwright produces trace/screenshot artifacts.

## Validation Commands
### Local (Base + E2E tokens)
1) Start stack:
   - `docker compose --profile gpu up -d`
   - `./scripts/smoke.sh`
2) Ensure deterministic data exists:
   - `./scripts/e2e_formats.sh` (or ingest at least one sample)
3) Run UI tests:
   - `cd ui/perplexica`
   - `npm ci` (or `npm install`)
   - `npm run test:e2e`

### Overlay (if UI depends on overlay-only capabilities)
- start overlay and re-run relevant tests:
  - `docker compose -f docker-compose.yml -f docker-compose.intelligence.yml --profile gpu up -d`
  - `./scripts/smoke.sh --overlay`
  - run E2E harness in overlay mode if needed
  - run UI E2E

## Risks / Failure Modes
- UI selectors are unstable -> mitigate via `data-testid`.
- UI needs seeded data -> mitigate via PRP-FMT-001 harness.
- Backend timing causes flakiness -> mitigate via waits for "results loaded" + timeouts + retries.

## Rollback Plan
- Tests are additive. If flaky initially:
  - mark UI E2E as non-blocking in CI temporarily (documented),
  - then harden until stable, then make blocking.

## Deliverables
- Playwright suite + testids
- docs/dev/ui-e2e-testing.md
- Optional validate integration flag
