# Implementation Plan - Setup Agent Workflow Layer

**Status:** Done
**Date:** 2026-01-12
**Context:** Establishing PIV Loop from Habit Tracker best practices.

## 1. Goal & Context
*   **What:** Implement `.claude/commands`, `AGENTS.md`, and `scripts/validate.ps1`.
*   **Why:** To standardize Agent behavior, reduce context load, and enforce validation.
*   **User Story:** As an AI Agent, I want clear instructions (rules) and tools (commands) so I can modify the repo safely.

## 2. Architecture & Design
*   **Components:**
    -   `AGENTS.md`: Global Rules.
    -   `.claude/commands/**`: Workflow instructions.
    -   `scripts/validate.ps1`: Unified entry point.
    -   `docs/agent/reference/**`: Context storage.

## 3. Implementation Steps (Execution)
- [x] **Step 1:** Create Directory Structure.
- [x] **Step 2:** Create `AGENTS.md`.
- [x] **Step 3:** Create Templates (`feature-plan.md`, `rca.md`).
- [x] **Step 4:** Implement `validate.ps1`.
- [x] **Step 5:** Create Slash Commands (Prime, Plan, Execute, Validate).
- [x] **Step 6:** Update `README.md`.

## 4. Verification Plan (Validate)
**Automated Tests:**
*   [x] Run `scripts/validate.ps1` -> Should pass Docker Config check.

**Manual Verification:**
*   [x] Check if `AGENTS.md` exists.
*   [x] Check if `README.md` has the Command Table.
