# E2E Format Harness (PRP-FMT-001)

This harness validates ingest -> index -> retrieve for a minimal, deterministic
sample set. It is intended for local runs and can be wired into validation later.

## Prereqs
- Docker services running (base or overlay).
- Qdrant and Neural Search API reachable.

## Commands

Base (core samples only):
```
python scripts/e2e_formats.py --mode base
```

Overlay (adds overlay-only samples + special-parser health check):
```
python scripts/e2e_formats.py --mode overlay
```

## Runtime Evidence (Cole-Medin Gate)

This harness is considered **Validated** only after both base and overlay runs
complete successfully and reports are generated.

Base stack:
```
docker compose --profile gpu up -d
./scripts/smoke.sh
./scripts/validate.sh
python scripts/e2e_formats.py --mode base --artifacts artifacts/e2e/base
```

Overlay stack:
```
docker compose -f docker-compose.yml -f docker-compose.intelligence.yml --profile gpu up -d
./scripts/smoke.sh --overlay
./scripts/validate.sh
python scripts/e2e_formats.py --mode overlay --artifacts artifacts/e2e/overlay
```

Evidence artifacts:
- `artifacts/e2e/base/e2e_formats_report.json`
- `artifacts/e2e/overlay/e2e_formats_report.json`
- Update `docs/PROJECT_STATUS.md` to `Done (Validated)` and link the artifacts + execute log.

## CLI
```
python scripts/e2e_formats.py [--mode base|overlay] [--ingest smart|indexer]
                             [--samples data/samples] [--artifacts artifacts/e2e]
                             [--timeout-min 20] [--poll-sec 5]
                             [--inbox PATH] [--archive-root PATH] [--quarantine-root PATH]
                             [--ledger PATH]
                             [--qdrant-url URL] [--qdrant-collection NAME] [--qdrant-api-key KEY]
                             [--search-url URL] [--search-limit 8]
                             [--keep-inbox] [--dry-run]
```

### Defaults
- `--mode base`
- `--samples data/samples`
- `--artifacts artifacts/e2e`
- `--timeout-min 20`
- `--poll-sec 5`
- `--search-url http://localhost:8040/api/neural-search`
- `--search-limit 8`
- `--qdrant-url http://localhost:6335`
- `--qdrant-collection neural_vault`
- `--qdrant-api-key` from `QDRANT_API_KEY`
- `--inbox` from `CONDUCTOR_INBOX` (fallback: `./data/inbox`)

### Exit codes
- `0`: all samples passed
- `1`: at least one sample failed
- `2`: prerequisites missing or unsafe inbox state

## Portability (Windows + WSL)
Examples:
- Windows: `CONDUCTOR_INBOX=F:\_Inbox`
- WSL: `CONDUCTOR_INBOX=/mnt/f/_Inbox`

For isolated testing, point inbox/archive/quarantine to a local folder:
```
python scripts/e2e_formats.py --inbox ./data/inbox --archive-root ./data/archive --quarantine-root ./data/quarantine
```

## Reports
Output is written to:
- `artifacts/e2e/e2e_formats_report.json`
- `artifacts/e2e/e2e_formats_report.md`

The JSON includes per-sample checks:
- `moved_or_quarantined`
- `ledger_entry`
- `qdrant_evidence`
- `search_retrieval`

`search_retrieval` uses a tiered assertion:
- **strong**: search source matches ledger current_path (path-level match)
- **medium**: token appears in excerpt/content/path/filename
- **weak**: Qdrant payload match (reported as warning; only allowed if completion 2-of-3 passed)

## Notes
- `smart_ingest.py` moves files out of the inbox. Use an isolated inbox if you
  do not want to touch real data.
- If a sample file is missing, the harness attempts to generate a tiny fixture.
