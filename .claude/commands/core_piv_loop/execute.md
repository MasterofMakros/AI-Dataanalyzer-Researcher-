---
description: "EXECUTE Phase: Implements the approved plan."
---

# Execute Phase

**Step 1: Load Plan**
Read the approved PRP from `PRPs/<slug>.md`.

**Step 2: Implementation Cycle**
For each step in the plan:
1.  **Code**: distinct, small changes.
2.  **Verify**: Run `scripts/validate.ps1` (or relevant subset).
3.  **Commit**: (Conceptual or actual git commit).

**Step 3: Pivot?**
If the plan turns out to be wrong:
- **STOP**.
- Update the PRP.
- Re-request approval.

**Step 4: Done**
When all steps are done and Validation Gates pass: proceed to **Validate**.
