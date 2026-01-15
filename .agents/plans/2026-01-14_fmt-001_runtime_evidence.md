# Runtime Evidence — PRP-FMT-001
Date: 2026-01-15
Host: Windows (runs executed via PowerShell/cmd.exe from WSL)

## Base run
Commands:
- docker compose --profile gpu up -d
- scripts/smoke.ps1
- scripts/validate.ps1
- python scripts/e2e_formats.py --mode base --inbox C:\\Users\\Admin\\Desktop\\AI-Dataanalyzer-Researcher-\\data\\inbox_e2e_run --archive-root C:\\Users\\Admin\\Desktop\\AI-Dataanalyzer-Researcher-\\data\\archive_e2e_run --quarantine-root C:\\Users\\Admin\\Desktop\\AI-Dataanalyzer-Researcher-\\data\\quarantine_e2e_run --ledger C:\\Users\\Admin\\Desktop\\AI-Dataanalyzer-Researcher-\\data\\conductor_root_e2e\\data\\shadow_ledger.db --artifacts artifacts/e2e/base

Results:
- docker version: not captured in WSL session (ran via Windows cmd.exe)
- docker compose version: not captured in WSL session (ran via Windows cmd.exe)
- smoke exit code: 0 (completed without errors)
- validate exit code: 0 (completed without errors)
- e2e exit code: 0
- e2e run: run_id=20260115_094205_3e2eee09 timestamp=2026-01-15T09:42:05Z
- summary: total=9 passed=9 failed=0 skipped=0
- artifacts:
  - artifacts/e2e/base/e2e_formats_report.json
  - artifacts/e2e/base/e2e_formats_report.md

## Overlay run
Commands:
- docker compose -f docker-compose.yml -f docker-compose.intelligence.yml --profile gpu up -d
- scripts/smoke.ps1 -Overlay
- scripts/validate.ps1
- python scripts/e2e_formats.py --mode overlay --inbox C:\\Users\\Admin\\Desktop\\AI-Dataanalyzer-Researcher-\\data\\inbox_e2e_overlay --archive-root C:\\Users\\Admin\\Desktop\\AI-Dataanalyzer-Researcher-\\data\\archive_e2e_overlay --quarantine-root C:\\Users\\Admin\\Desktop\\AI-Dataanalyzer-Researcher-\\data\\quarantine_e2e_overlay --ledger C:\\Users\\Admin\\Desktop\\AI-Dataanalyzer-Researcher-\\data\\conductor_root_e2e_overlay\\data\\shadow_ledger.db --artifacts artifacts/e2e/overlay

Results:
- smoke exit code: 0 (completed without errors)
- validate exit code: 0 (completed without errors)
- e2e exit code: 0
- e2e run: run_id=20260115_113646_e45939df timestamp=2026-01-15T11:36:46Z
- summary: total=11 passed=11 failed=0 skipped=0
- artifacts:
  - artifacts/e2e/overlay/e2e_formats_report.json
  - artifacts/e2e/overlay/e2e_formats_report.md

## Notes / Issues
- Search retrieval checks completed with weak (qdrant fallback) matches; reported in JSON.
