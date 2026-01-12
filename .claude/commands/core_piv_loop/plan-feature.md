---
description: "PLAN Phase: Creates a structured Implementation Plan."
---

# Plan Phase

**Step 1: Create Plan File**
Create a new file in `.agents/plans/` named `YYYY-MM-DD_<feature-slug>.md`.
Copy the content from `.agents/plans/_templates/feature-plan.md`.

**Step 2: Fill Definition**
- **Context:** Why are we doing this?
- **Proposed Changes:** Which files? Which Docker services?
- **Verification:** How will we prove it works? (Must include `validate.ps1`).

**Step 3: Review**
Present the plan to the User.
**Do NOT proceed to execution until the user approves the plan.**
