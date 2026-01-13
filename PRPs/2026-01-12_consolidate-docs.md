# PRP: Documentation Consolidation (Cole-Style)

Status: planned

## Context
Root directory has ~25 Markdown files, causing navigation overhead. Goal: minimal root (~10 files), everything else in `docs/`.

## Goal
Consolidate all non-essential Markdown files from root to `docs/` without losing information.

---

## Target Root Structure (After)
```
README.md
CLAUDE.md
INITIAL.md
LICENSE
CONTRIBUTING.md
SECURITY.md
CHANGELOG.md
.env.example
.gitignore
requirements.txt
docker-compose*.yml (3 files)
```

---

## Execution Steps

### Step 1: Create docs/ Substructure
```bash
mkdir -p docs/architecture docs/strategy docs/product docs/project docs/_archive/audits
```

### Step 2: Move Files (git mv for history)

| Source | Destination |
|:---|:---|
| `ARCHITECTURE.md` | `docs/architecture/overview.md` |
| `tech-stack.md` | `docs/architecture/tech_stack.md` |
| `DATA_STRATEGY_DEEP_DIVE.md` | `docs/strategy/data_strategy.md` |
| `VISION.md` | `docs/product/vision.md` |
| `USER_VALUE_SCENARIOS.md` | `docs/product/user_value_scenarios.md` |
| `product.md` | `docs/product/index.md` |
| `product-guidelines.md` | Merge into `docs/product/index.md` |
| `PROJECT_OVERVIEW_2025.md` | `docs/project/overview_2025.md` |
| `IMPROVEMENT_RECOMMENDATIONS_2025.md` | `docs/project/improvements_2025.md` |
| `workflow.md` | `docs/dev/workflow.md` |
| `tracks.md` | `docs/dev/tracks.md` |
| `AGENT_CONTEXT.md` | Merge into `CLAUDE.md` |
| `README_PI.md` | Merge into `README.md` |
| `REPO_READINESS_AUDIT_*.md` | `docs/_archive/audits/` |

### Step 3: Create docs/index.md (Navigation Hub)
```markdown
# Documentation Index

## Architecture
- [Overview](architecture/overview.md)
- [Tech Stack](architecture/tech_stack.md)

## Product
- [Vision](product/vision.md)
- [User Value Scenarios](product/user_value_scenarios.md)

## Project
- [Overview 2025](project/overview_2025.md)
- [Improvements 2025](project/improvements_2025.md)

## Development
- [Workflow](dev/workflow.md)
- [ADRs](ADR/)

## Archive
- [Audits](_archive/audits/)
```

### Step 4: Update Internal Links
```bash
rg -l "ARCHITECTURE.md|tech-stack.md|VISION.md" . --glob "*.md"
```
Update all internal links to new paths.

---

## Acceptance Criteria
- [ ] Root has ≤12 files
- [ ] `docs/index.md` exists with navigation
- [ ] All moved files accessible via new paths
- [ ] No broken internal links
- [ ] `scripts/validate.ps1` passes

## Rollback
```bash
git checkout HEAD~1 -- .
```
