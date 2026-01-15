# UI E2E Testing (PRP-UI-002)

## Prerequisites
- Base stack running (`docker compose --profile gpu up -d`).
- Deterministic data seeded via PRP-FMT-001 (so E2E_TOKEN_* queries resolve).
- UI reachable at `http://localhost:3100` (override with `E2E_UI_BASE_URL`).

## Recommended workflow
```bash
docker compose --profile gpu up -d
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
