---
description: "Initialize the project environment."
---

# Init Project

**Step 1: Environment**
-   Check if `.env` exists. If not, copy `.env.example`.
-   Verify `.env` values (API keys placeholders).

**Step 2: Perplexica Frontend**
-   Navigate to `ui/perplexica`.
-   Run `npm install` (necessary for IDE support).

**Step 3: Docker**
-   Identify appropriate profile (`gpu`, `cpu`, or `intelligence`).
-   Start services: `docker compose up -d` (or with profile).

**Step 4: Validation**
-   Run `/validation:validate`.
