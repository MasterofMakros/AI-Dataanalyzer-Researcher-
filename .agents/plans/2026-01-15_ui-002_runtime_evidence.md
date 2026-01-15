# Runtime Evidence — PRP-UI-002
Date: 2026-01-15

## Run 1 (WSL, prereq failure)
Host: WSL (no Docker CLI available in this environment)
Node: v20.18.1 (/tmp/node-20.18.1; system node not in PATH)
npm: 10.8.2
Docker: docker CLI not available (docker version failed)
Docker Compose: docker CLI not available (docker compose version failed)

Base stack:
- docker compose --profile gpu up -d (not run; docker CLI unavailable)
- ./scripts/smoke.sh (not run; docker CLI unavailable)
- python3 scripts/e2e_formats.py --mode base --artifacts artifacts/e2e/base
- e2e exit code: 1
- report: artifacts/e2e/base/e2e_formats_report.json (summary: total=9 passed=0 failed=9)
- report: artifacts/e2e/base/e2e_formats_report.md
- errors: smart_ingest_failed for all samples (services not running)

UI E2E:
- PATH=/tmp/node-20.18.1/bin:$PATH npm ci (exit 0)
- PATH=/tmp/node-20.18.1/bin:$PATH npm run test:e2e (exit 1)
- failure: search-input not found after page.goto('/') (UI not running)
- artifacts: ui/perplexica/playwright-report/, ui/perplexica/test-results/

## Run 2 (Windows PowerShell log: artifacts\\evidence\\ui-002_runtime_2026-01-15_19-20-51.log)
Host: Windows PowerShell
Docker: 29.1.3 (Docker Desktop 4.56.0)
Docker Compose: v5.0.0-desktop.1
Node: v22.18.0
npm: 10.9.3

Base stack:
- docker compose --profile gpu up -d (exit -1 due to warning on stderr about orphan containers)
- docker compose ps shows running stack; notable states:
  - conductor-perplexica: unhealthy
  - conductor-db-parser: restarting
  - conductor-metadata-extractor: restarting
  - special-parser: unhealthy

Smoke:
- scripts/smoke.ps1 exit: 0
- results: 8 passed, 0 failed, 1 skipped (Conductor API warn)

Seed (FMT-001 harness):
- python scripts\\e2e_formats.py --mode base --artifacts artifacts\\e2e\\base
- exit: 2
- error: Inbox is not empty; refusing to run without --keep-inbox.

UI E2E:
- npm ci exit: -1 (warnings emitted to stderr; PowerShell NativeCommandError)
- npx playwright install --with-deps exit: 0
- npm run test:e2e exit: 1
- failures:
  - search-input not found after page.goto('/') (7 tests)
  - error-banner not found (error_state_backend_down)
- artifacts: ui/perplexica/playwright-report/, ui/perplexica/test-results/

## Notes / Issues
- PowerShell 5.1 treats stderr output as an error when $ErrorActionPreference=Stop. Use cmd.exe with 2>&1 or relax error handling to avoid false negatives.
- Clean seed requires an empty inbox (or pass --keep-inbox).
- UI E2E needs a healthy UI at http://localhost:3100 and a container image matching the current testids.

## Run 3 (Windows PowerShell manual run, 2026-01-15)
Host: Windows PowerShell
Node: v22.18.0
npm: 10.9.3

Seed (dedicated inbox):
- python scripts\\e2e_formats.py --mode base --inbox artifacts\\inbox_ui_e2e --archive-root artifacts\\archive_ui_e2e --quarantine-root artifacts\\quarantine_ui_e2e --artifacts artifacts\\e2e\\base
- report: artifacts/e2e/base/e2e_formats_report.json
- summary: total=9 passed=0 failed=9
- errors: smart_ingest_failed: exit=1 for all samples

UI image build:
- docker compose build perplexica failed (node:24.5.0-slim metadata lease error; transient)
- docker compose up -d --force-recreate --build perplexica failed
  - yarn install --frozen-lockfile: lockfile out of date

UI E2E:
- npm run test:e2e executed from repo root
- failure: ENOENT for package.json (run should be from ui\\perplexica)

## Follow-up actions
- Update ui/perplexica/yarn.lock to match package.json (Playwright deps), then rebuild the UI image.
- Re-run npm run test:e2e from ui\\perplexica with E2E_UI_BASE_URL=http://localhost:3100.
