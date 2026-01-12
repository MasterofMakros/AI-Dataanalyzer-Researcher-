---
description: "Generate a PRP from INITIAL.md"
---

# Generate PRP

**Step 1: Read INITIAL.md**
Read `INITIAL.md` (or the issue text provided).

**Step 2: Create File**
Create `PRPs/<feature-slug>.md` from `PRPs/templates/prp_base.md`.

**Step 3: Fill Context**
- **Goal:** From Feature description.
- **Repo Facts:** Check `examples/` and `CLAUDE.md`.
- **Implementation Plan:** Break down into atomic steps.
- **Validations:** Must include `./scripts/validate.ps1`.

**Step 4: Output**
Present the new file path to the user.
