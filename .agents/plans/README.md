# Agent Plans

This directory contains the operational plans for the AI Agents working on this repository.
The workflow follows the **PIV Loop** (Prime → Plan → Execute → Validate).

## Convention
- **Filename:** `YYYY-MM-DD_<short-slug>.md` (e.g., `2026-01-12_setup-agent-layer.md`)
- **Format:** Markdown, following the templates in `_templates/`.
- **Status:** Plans are immutable documentation of *intent*. If a plan changes drastically, create a new one or append an update section.

## Usage
1.  **Analyze** the request.
2.  **Generate** a plan file using `/core_piv_loop:plan-feature`.
3.  **Review** with the user (Plan Phase).
4.  **Execute** based on the stored plan.
