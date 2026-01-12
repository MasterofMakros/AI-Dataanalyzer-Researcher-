---
description: "Generate a report after execution."
---

# Execution Report

**Step 1: Gather Stats**
- Which files changed?
- Did `validate.ps1` pass?

**Step 2: Write Report**
Create `.agents/reports/YYYY-MM-DD_execution_report.md`.
Template:
```markdown
# Execution Report: <Feature>
**Status:** Success/Fail
**Validation:** Passed
**Files Changed:**
- ...
**Notes:**
- ...
```
