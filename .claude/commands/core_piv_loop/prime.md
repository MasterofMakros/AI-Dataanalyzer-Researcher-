---
description: "PRIME Phase: Loads context and rules to prepare for a task."
---

# Prime Phase

**Step 1: Load Global Context**
Read the following files to establish the "North Star" and global constraints:
- `AGENTS.md` (Global Rules)
- `docs/agent/reference/_index.md` (Reference Index)

**Step 2: Identify Reachable Context**
Based on the user's request, identify which services are involved?
- **Frontend?** Read `docs/agent/reference/services.md` and check `ui/perplexica`.
- **Backend?** Check `conductor-api` or `neural-search-api`.
- **Ingestion?** Check `docker/workers`.

**Step 3: Acknowledge**
Confirm that you have loaded the context and are ready to proceed to the **Plan** phase.
State your understanding of the user's goal.
