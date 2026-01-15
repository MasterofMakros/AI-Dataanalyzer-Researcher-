# Runtime Evidence — PRP-UI-002
Date: 2026-01-15
Host: WSL (no Docker CLI available in this environment)
Node: v20.18.1 (/tmp/node-20.18.1; system node not in PATH)
npm: 10.8.2
Docker: docker CLI not available (docker version failed)
Docker Compose: docker CLI not available (docker compose version failed)

## Base stack
Commands:
- docker compose --profile gpu up -d (not run; docker CLI unavailable)
- ./scripts/smoke.sh (not run; docker CLI unavailable)
- python3 scripts/e2e_formats.py --mode base --artifacts artifacts/e2e/base

Results:
- e2e exit code: 1
- report: artifacts/e2e/base/e2e_formats_report.json (summary: total=9 passed=0 failed=9)
- report: artifacts/e2e/base/e2e_formats_report.md
- errors: smart_ingest_failed for all samples (services not running)

## UI E2E
Commands:
- cd ui/perplexica
- PATH=/tmp/node-20.18.1/bin:$PATH npm ci
- PATH=/tmp/node-20.18.1/bin:$PATH npm run test:e2e

Results:
- npm ci exit code: 0
- test:e2e exit code: 1
- failure: search-input not found after page.goto('/') (UI not running)
- artifacts:
  - ui/perplexica/playwright-report/
  - ui/perplexica/test-results/

## Notes / Issues
- Docker CLI is unavailable in this environment; base stack not started and seed run failed.
- UI E2E requires the UI to be reachable at http://localhost:3100 (or E2E_UI_BASE_URL).
- Re-run after Docker is available and base stack is up.
