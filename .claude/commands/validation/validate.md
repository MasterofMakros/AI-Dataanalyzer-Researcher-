---
description: "VALIDATE Phase: Runs the standard validation suite."
---

# Validate Phase

**Step 1: Run Full Suite**
Execute:
```powershell
./scripts/validate.ps1
```

**Step 2: Analyze**
- **Docker Config Check:** Must be OK.
- **Doctor Check:** Must be OK.
- **Tests:** `pytest` should pass (if backend touched).
- **Build:** `npm run build` should pass (if frontend touched).

**Step 3: Report**
- If green: "Validation Passed."
- If red: "Validation Failed. Fix required."
