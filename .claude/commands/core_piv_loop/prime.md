---
description: "PRIME Phase: Loads context and rules to prepare for a task."
---

# Prime Phase

**Step 1: Repo Map & Rules**
Read `CLAUDE.md` to establish the "North Star" and global constraints.
Read `docs/agent/reference/_index.md` (if exists) or scan `README.md`.

**Step 2: Identify Reachable Context**
Based on the `INITIAL.md` or user request:
- **Frontend?** Check `ui/perplexica`.
- **Backend?** Check `docker/conductor-api`.
- **Infrastructure?** Check `docker-compose.yml`.

**Step 3: Assumption Check**
- Do I have the right ports? (Check `README.md`)
- Do I know the validation gates? (Check `CLAUDE.md`)

**Step 4: Acknowledge**
State: "Context Loaded. Ready to Plan."
