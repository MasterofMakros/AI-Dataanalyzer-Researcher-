# Product Guidelines & System Standards

## 1. File System UX (The "Interface")
Since the file system **is** the product, these rules apply to all folder structures:
*   **Max Depth**: 4 Levels (Pool -> Category -> Archive -> Files). Deep nesting confuses AI and Users.
*   **Naming**: `YYYY-MM-DD_Descriptive_Name` is the Gold Standard.
*   **Special Characters**: Avoid spaces ` ` (use `_`), umlauts `äöü` (use `ae`), and symbols `&%$`. (Exceptions: Display names in File Explorer).
*   **"Inbox Zero"**: No files live in Root `F:\` or Pool Roots (e.g., `F:\09 Projekte\`). They must be in subfolders.

## 2. AI Interaction Standards
*   **Context First**: Every significant directory (>10 files) MUST have a `_context.md`.
*   **Read-Only Default**: AI Agents (RAG) mount the drive as Read-Only. Only specific "Janitor Scripts" have Write access.
*   **Privacy Boundary**: Personal Pools (01-08) and Finance (10) are **Local Only**. No API context injection unless explicitly authorized via "Hybrid Protocol".

## 3. Automation Philosophy
*   **Silent Success**: Scripts should run silently and only report errors or "Mission Accomplished".
*   **Git Logging**: Every script that modifies files MUST log to `F:\.migration_manifest`.
*   **Idempotency**: Scripts must be runnable multiple times without causing duplicate files or side effects.
