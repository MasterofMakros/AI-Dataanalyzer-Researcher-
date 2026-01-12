---
description: "Execute a PRP with strict validation loops."
---

# Execute PRP

**Step 1: Read PRP**
Load `PRPs/<feature-slug>.md`.

**Step 2: Execute Loop**
For each Implementation Step:
1.  **Read** relevant repo files.
2.  **Edit** code.
3.  **Run** Validation: `./scripts/validate.ps1`.
    - If fail: **Fix immediately**. Do not proceed.
4.  **Mark** step as done in PRP.

**Step 3: Final Report**
Update `PRPs/<feature-slug>.md` status to "Done".
Run `/validation:execution-report`.
