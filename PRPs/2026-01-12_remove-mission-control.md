# PRP: Remove Mission Control UI Completely

## Context
Mission Control (`apps/mission-control`) is a legacy Admin Dashboard that duplicates functionality available via Orchestrator API (:8020) and Perplexica. Per user decision, only Perplexica UI should remain.

## Goal
Remove Mission Control UI completely without breaking remaining functionality.

---

## Pre-Flight (Safety Net)

### 1. Create Rollback Tag
```bash
git tag pre-remove-mission-control
```

### 2. Find All References
```bash
rg -n "Mission Control|mission_control|mission-control|localhost:3000|:3000" .
```

### 3. Categorize Findings
- [ ] docker-compose*.yml
- [ ] scripts/
- [ ] .github/workflows/
- [ ] docs/
- [ ] README.md
- [ ] PRPs/examples/

---

## Execution Steps

### Step 1: Remove from Docker Compose
Edit `docker-compose.yml`:
- Remove `mission-control` service block
- Remove any `depends_on: mission-control`
- Remove port `3000` mapping

**Validation:** `docker compose config -q`

### Step 2: Remove UI Code
```bash
git rm -rf apps/mission-control
```

### Step 3: Update CI Workflow
Edit `.github/workflows/ci.yml`:
- Remove any `mission_control` or `apps/mission-control` references
- Update frontend job to only build Perplexica

### Step 4: Update README
- Remove Mission Control from service table (Port 3000)
- Remove from architecture diagram if present
- Update "Überprüfung" section

### Step 5: Update Documentation
Search and update in `docs/`:
- Any references to Mission Control
- Architecture diagrams
- Port listings

---

## Acceptance Criteria
- [ ] `docker compose config -q` passes
- [ ] `docker compose up -d` starts without Mission Control
- [ ] Perplexica (:3100) is accessible
- [ ] README has no Mission Control references
- [ ] CI workflow passes

## Rollback
```bash
git checkout pre-remove-mission-control
```
