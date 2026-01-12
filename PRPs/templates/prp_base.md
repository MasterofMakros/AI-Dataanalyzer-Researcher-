# PRP: <Feature Name>

## Goal
- ...

## Non-Goals
- ...

## Current State (Repo Facts)
- Observed files:
- Current commands:
- Constraints:

## Requirements (Functional)
- MUST ...
- MUST ...
- SHOULD ...
- CAN ...

## Requirements (Non-Functional)
- Reliability:
- Performance:
- Security/privacy (local-first):
- Operability (logs, health endpoints):

## Implementation Plan (Step-by-step)
1) Prime: gather context + confirm assumptions
2) Implement: small commits, update tests
3) Validate: run gates, fix failures
4) Document: update README/docs/ADRs if needed

## Validation Gates (MUST PASS)
- `./scripts/validate.ps1`
- Any extra service checks:
  - `curl -f http://localhost:8010/health`
  - `curl -f http://localhost:8020/health`

## Risks & Rollback
- Risk:
- Mitigation:
- Rollback plan:

## Definition of Done
- [ ] All gates pass
- [ ] Docs updated
- [ ] No unresolved TODOs
- [ ] Changes are minimal and reviewed
