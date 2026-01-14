# PRP-FMT-001: E2E Format Coverage Harness (123~ Formats) - Ingest -> Index -> Retrieve

## Status
- State: planned
- Owner: codex
- Last Updated: 2026-01-14

## Purpose
Add a deterministic end-to-end test harness that proves the system can ingest representative files, extract content (incl. OCR/transcription where applicable), index them (Qdrant), and retrieve them via the Search API/UI stack.

## Background / Problem
Current validation covers:
- Compose config validity (base + overlay)
- Service reachability (smoke)
But does NOT prove:
- ingestion works across format classes,
- extraction/OCR/transcription produces usable content,
- content is embedded + indexed,
- retrieval returns correct sources.

We need a small, versioned test set + scripts that run locally and in CI (where possible) to prevent regressions and doc drift.

## Scope (Goals)
1) Create a small canonical sample set covering all major format classes:
   - Text docs, PDFs, scanned PDFs/images (OCR), spreadsheets/presentations, HTML, email,
     audio (transcribe), video (audio extraction + transcribe), archives, structured data.
2) Provide an E2E runner script (bash + PowerShell OR a single Python runner) that:
   - starts required stack (base or overlay),
   - ingests samples,
   - waits for completion,
   - asserts artifacts exist,
   - asserts Qdrant index count increased,
   - asserts Search API returns expected sources/snippets.
3) Make tests overlay-aware:
   - Base: core formats.
   - Overlay: additionally test 3D/CAD/GIS/Fonts via special-parser.
4) Produce evidence artifacts:
   - a machine-readable test report (JSON),
   - a human summary (Markdown) for `.agents/plans/`.

## Non-Goals
- Exhaustive testing of every extension in the claimed "123 formats".
  We test representative files per format class and enforce that the extension mapping
  stays consistent.
- Performance/load benchmarking.
- UI flow testing (covered in PRP-UI-002).

## Repository Additions / File Layout
- `data/samples/` (versioned; tiny fixtures only)
  - `text/` (txt, md, html, json, csv)
  - `office/` (docx, xlsx, pptx)
  - `pdf/` (text-pdf, scanned-pdf)
  - `email/` (eml)
  - `image/` (png/jpg)
  - `audio/` (wav/mp3 short)
  - `video/` (mp4 short)
  - `archive/` (zip with inner files)
  - `overlay_only/` (3d/cad/gis/fonts minimal fixtures)
- `scripts/e2e_formats.sh`
- `scripts/e2e_formats.ps1`
  OR (preferred for determinism):
- `scripts/e2e_formats.py` (single runner) + wrappers in sh/ps1

- `docs/dev/e2e-testing.md` (how to run, prereqs, expected outputs)
- Optional: `docs/reference/format-coverage.md` (mapping: format class -> sample -> processor)

## Verified Facts (from PRIME)
### Ingestion Contract (Primary + Fallback)
Primary (host-run, file-drop):
- Ingest by copying files into `CONDUCTOR_INBOX` (default `F:\_Inbox`).
- Run `python scripts/smart_ingest.py --once`.
- This writes Shadow Ledger and indexes into Qdrant collection `neural_vault`.

Fallback (direct indexer):
- Run `python scripts/file_indexer.py --path <folder> --limit N`.
- This indexes directly into Qdrant without Shadow Ledger or file move.

### Qdrant Details
- QDRANT_URL default: `http://localhost:6335`.
- Collection: `neural_vault` (hardcoded in `smart_ingest.py` and `file_indexer.py`).
- If `QDRANT_API_KEY` is set, send header `api-key: <key>`.

### Retrieval Contract (query-specific)
- Preferred endpoint: `POST http://localhost:8040/api/neural-search`.
- Assertion should check `sources[]` for the unique token in `excerpt` or a file reference
  in `filename` or `path`.

## Assumptions / Constraints
- Core services are reachable at:
  - Conductor API `http://localhost:8010`
  - Neural Search API `http://localhost:8040`
  - Orchestrator `http://localhost:8020`
  - Qdrant `http://localhost:6335`
- Overlay special-parser (if enabled) is on host `8016 -> 8015` and health at:
  - `http://localhost:8016/health`

- The harness runs host-side (not inside the conductor-api container) because the
  F: mount is currently disabled for conductor-api in compose. If containerized
  ingestion is desired later, create a separate PRP to enable mounts safely.
- Do not use `smart_ingest_v2.py` (referenced in docs but not present in repo).
- Portability: do not hardcode `F:\` paths. Use env + CLI args:
  - `CONDUCTOR_INBOX` (inbox path)
  - `CONDUCTOR_ARCHIVE` (archive root)
  - `CONDUCTOR_QUARANTINE` (quarantine root)
  - `CONDUCTOR_ROOT` (base path; ledger is `${CONDUCTOR_ROOT}/data/shadow_ledger.db`)
  - Runner should also accept `--inbox`, `--archive-root`, `--quarantine-root`,
    `--ledger-path` overrides.
  - Windows example: `F:\_Inbox`
  - WSL example: `/mnt/f/_Inbox` (or `./data/inbox` if mapped locally)

## Implementation Plan (Ordered)
1) Encode the verified ingestion contract in the runner:
   - Primary: file-drop to `CONDUCTOR_INBOX` + run `smart_ingest.py --once`.
   - Fallback: `file_indexer.py --path --limit`.
   - Implement a small adapter layer to switch between these two modes.
2) Create `data/samples/`:
   - Generate minimal fixtures where possible via script (preferred).
   - Store only tiny artifacts (KB to a few MB).
   Suggested minimum sample list (core):
   - `text/plain`: `hello.txt` (contains unique token `E2E_TOKEN_TXT`)
   - `markdown`: `note.md` (`E2E_TOKEN_MD`)
   - `html`: `page.html` (`E2E_TOKEN_HTML`)
   - `json`: `sample.json` (`E2E_TOKEN_JSON`)
   - `csv`: `sample.csv` (`E2E_TOKEN_CSV`)
   - `pdf/text`: `text.pdf` (`E2E_TOKEN_PDF_TEXT`)
   - `pdf/scanned`: `scan.pdf` with raster text `E2E_TOKEN_PDF_OCR`
   - `image/png`: `image.png` containing visible text `E2E_TOKEN_IMG_OCR`
   - `docx`: `doc.docx` (`E2E_TOKEN_DOCX`)
   - `xlsx`: `sheet.xlsx` (`E2E_TOKEN_XLSX`)
   - `pptx`: `deck.pptx` (`E2E_TOKEN_PPTX`)
   - `eml`: `mail.eml` (`E2E_TOKEN_EML`)
   - `audio/wav`: 2-5s wav with spoken "E2E TOKEN AUDIO"
   - `video/mp4`: 2-5s mp4 with spoken "E2E TOKEN VIDEO"
   - `zip`: zip containing `hello.txt` and `note.md`
   Overlay-only samples (minimal):
   - `fonts`: a small .ttf or .otf (if parser supports; else keep placeholder)
   - `3D`: `cube.stl` (tiny)
   - `CAD`: `part.step` (tiny) OR a supported CAD format by parser
   - `GIS`: `point.geojson` OR a supported GIS file by parser
3) Implement runner (Python recommended):
   - Inputs:
     - mode: `base` or `overlay`
     - samples root
     - timeouts (default 10-20 min)
     - inbox/archive/quarantine/ledger overrides (env + CLI)
   - Steps:
     a) Assert required services are reachable (use existing smoke endpoints)
     b) For each sample:
        - ingest
        - assert completion using at least 2-of-3 signals:
          - Move/Quarantine: file no longer in inbox and exists in archive or quarantine
          - Shadow Ledger: `files` table has entry for filename/hash with status in
            {indexed, quarantined}
          - Qdrant: count increased OR payload found via scroll using file path/name/token
     c) Qdrant assertions:
        - capture pre-count for `neural_vault`
        - post-ingest count increased by >= N
        - if `QDRANT_API_KEY` set, include `api-key` header
     d) Retrieval assertions:
        - query Neural Search API with unique token (e.g. `E2E_TOKEN_DOCX`)
        - assert `sources[]` contains the token in `excerpt` OR references the file
          in `filename` or `path`
   - Output:
     - `artifacts/e2e_formats_report.json`
     - `artifacts/e2e_formats_report.md`
4) Provide wrappers:
   - `scripts/e2e_formats.sh` calls the Python runner
   - `scripts/e2e_formats.ps1` calls the Python runner
5) Add base vs overlay behavior:
   - Base: core samples only
   - Overlay: add overlay-only samples and check `special-parser` health
6) Integrate with validation:
   - Add an optional gate in `scripts/validate.*`:
     - `--e2e` runs `e2e_formats` (not default if too slow)
   - Document commands in `docs/dev/e2e-testing.md`
7) Update docs:
   - `docs/PROJECT_STATUS.md` add entry "E2E Format Harness"
   - Add/Update `docs/architecture/service-matrix.md` note about overlay-only parsing coverage

## Blocking Decisions
None (resolved in PRIME).

## Acceptance Criteria (Testable)
- [ ] `scripts/e2e_formats.(sh|ps1)` runs in base mode and passes on a healthy local setup.
- [ ] `scripts/e2e_formats.(sh|ps1) --overlay` passes when overlay is started and special-parser is healthy.
- [ ] Runner produces JSON + Markdown reports under an artifacts directory.
- [ ] Retrieval assertions are tiered and reported:
      - **Strong:** search result matches ledger-derived identifier (current_path and/or hash if exposed).
      - **Medium:** token appears in excerpt/content/metadata fields.
      - **Weak (warning only):** Qdrant payload match accepted *only* if completion 2-of-3 passed.
      The report must include `checks.search_retrieval.level` and `matched_on`.
- [ ] Overlay-only samples are:
      - either processed and retrievable in overlay mode,
      - or explicitly marked "skipped with reason" if unsupported by parser (no silent pass).
- [ ] No large binary artifacts are committed (samples stay small).

## Validation Commands
### Base
- `docker compose --profile gpu up -d`
- `./scripts/smoke.sh`
- `./scripts/validate.sh`
- `./scripts/e2e_formats.sh`

### Overlay
- `docker compose -f docker-compose.yml -f docker-compose.intelligence.yml --profile gpu up -d`
- `./scripts/smoke.sh --overlay`
- `./scripts/validate.sh`
- `./scripts/e2e_formats.sh --overlay`

(Windows equivalents: `.ps1`)

## Risks / Failure Modes
- Retrieval uses Qdrant scroll; mitigate with unique tokens and strict source assertions.
- OCR/transcription dependencies (tesseract/ffmpeg/whisper) cause flakiness -> mitigate by small samples + generous timeouts + stable "processed" checks.
- Qdrant assertions too brittle if collections vary -> mitigate by focusing on "count increased" + query-based assertions.
- `smart_ingest_v2.py` is referenced in docs but missing in repo -> do not depend on it.
- Conductor API does not mount F: -> harness must run host-side until mounts are re-enabled.

## Rollback Plan
- Runner and samples are additive. If failing in CI/local unexpectedly:
  - disable `--e2e` in validate default path
  - keep harness available as manual command until stabilized.

## Deliverables
- New `data/samples/` + runner scripts + docs
- E2E report artifacts
- Update to `docs/PROJECT_STATUS.md` and optional coverage doc
