# 🛠️ REMEDIATION PLAYBOOK (V3.0 Compliance)

**Objective:** Execute "Supreme Audit" clarifications and fixes.
**Execution Date:** 2026-01-07

---

## 1. Governance Remediation

### ✅ 1.1 Formalize De-Facto Decisions (ADRs)
- **Action:** Created `ADR-018` for PDF Parsing (Tika vs Docling).
- **Action:** Created `ADR-019` for Vector Database (Qdrant vs LanceDB).
- **Status:** **DONE**. Files exist in `docs/ADR/`.

### ✅ 1.2 Enforce Constitution (ANTI-ROADMAP)
- **Action:** Added specific exception clause for "TinyBERT" Reranking (<100ms) to `ANTI-ROADMAP.md`.
- **Status:** **DONE**.

---

## 2. Security & Infrastructure Hardening

### ✅ 2.1 Production Configuration
- **Action:** Generated `docker-compose.prod.yml` from the verified base compose.
- **Hardening Applied:**
    - **Bound Ports:** `127.0.0.1:6333` (Qdrant), `127.0.0.1:7700` (Meili).
    - **Pinned Versions:** `qdrant/qdrant:v1.15.5`, `getmeili/meilisearch:v1.23.0`.
- **Status:** **DONE**.

### ✅ 2.2 File System Sanitation
- **Action:** Moved root `_legacy` folder to `docs/_legacy/V2_SOURCE_ARCHIVE` to prevent confusion with active code.
- **Status:** **DONE**.

---

## 3. Documentation Sanitation

### ✅ 3.1 README Cleanup
- **Action:** Removed strikethrough/legacy links that pointed to dead files (`NEURAL_SEARCH_IMPLEMENTATION.md`).
- **Status:** **DONE**.

---

## 4. Verification Checklist

- [x] **Git Check:** `git status` is clean.
- [x] **File Check:** `docker-compose.prod.yml` exists.
- [x] **Content Check:** `ANTI-ROADMAP.md` contains "TinyBERT".
- [x] **Structure Check:** `_legacy` is GONE from root.

---

## 5. Deployment Instructions

To launch the strictly compliant production stack:

```bash
# 1. Pull latest images (pinned)
docker compose -f docker-compose.prod.yml pull

# 2. Start Stack (Detached)
docker compose -f docker-compose.prod.yml up -d

# 3. Verify Health
curl http://localhost:8000/health
```

---

**End of Playbook.**
