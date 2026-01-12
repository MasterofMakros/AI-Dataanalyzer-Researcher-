---
description: "Execute a PRP (Implementation Phase)"
---

# Execute PRP

**Step 1: Read PRP**
Load the approved PRP file from `PRPs/<feature-slug>.md`.

**Step 2: Implementation Loop**
For each step in the **Implementation Plan**:
1.  Read the relevant files/examples.
2.  Apply changes.
3.  **Run Validation Gates** (`scripts/validate.ps1`).
    - If fail: Fix bugs immediately.
    - If pass: Mark step as done.

**Step 3: Final Verification**
Run the full `Acceptance Criteria` checklist.
