# UI E2E Testing (PRP-UI-002)

## Prerequisites
- Base stack running (`docker compose --profile gpu up -d`).
- Deterministic data seeded via PRP-FMT-001 (so E2E_TOKEN_* queries resolve).
- UI reachable at `http://localhost:3100` (override with `E2E_UI_BASE_URL`).

## Recommended workflow
```bash
docker compose --profile gpu up -d --remove-orphans
./scripts/smoke.sh
python scripts/e2e_formats.py --mode base --artifacts artifacts/e2e/base

cd ui/perplexica
npm ci
npm run test:e2e
```

## Optional overrides
- `E2E_UI_BASE_URL=http://localhost:3100` to target a different UI host.

## Notes
- Tests rely on `data-testid` selectors for stability.
- Media preview tests skip when no audio/video/image sources are available.
- On failure, Playwright stores traces/screenshots/videos in `test-results/`.

## Windows PowerShell notes
- If `e2e_formats.py` reports “Inbox is not empty”, use a dedicated inbox path (e.g. `--inbox artifacts\\inbox_ui_e2e`) or clear the inbox before running.
- If PowerShell is set to `$ErrorActionPreference="Stop"`, warnings written to stderr can appear as failures. Prefer running native commands via `cmd.exe /c` with `2>&1` when logging.
- Ensure the UI container matches the current testids. If in doubt, rebuild the UI service:
  - `docker compose build perplexica`
  - `docker compose up -d --force-recreate --build perplexica`
- Avoid running Windows drive-letter paths inside WSL from the repo root; it can create a `F:` directory locally. If it appears, delete it from the repo root.
