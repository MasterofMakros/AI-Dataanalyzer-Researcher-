---
description: "RCA: Root Cause Analysis for bugs."
---

# Root Cause Analysis

**Step 1: Create Analysis Document**
Create a new file in `.agents/plans/` named `YYYY-MM-DD_rca_<bug-slug>.md`.
Copy content from `.agents/plans/_templates/rca.md`.

**Step 2: Investigate**
- **Do NOT fix yet.**
- Reproduce the issue.
- Find the code responsible.
- Answer: *Why was this code written this way? What constraint was missing?*

**Step 3: Propose Fix**
In the same document, outline the fix and the **Prevention** measure (e.g. "Add test case X").
