---
description: "VALIDATE Phase: Runs the standard validation suite."
---

# Validate Phase

**Step 1: Run Validation Script**
Execute the unified validation entry point:
```powershell
./scripts/validate.ps1
```

**Step 2: Interpret Results**
- **Docker Config:** Must be valid.
- **Tests:** `pytest` must pass (if backend changes made).
- **Health:** Services must be responding (if changes deployed).

**Step 3: Report**
Summarize the validation results.
- If Success: Ready for commit.
- If Fail: Back to **Execute** phase (fix bugs).
