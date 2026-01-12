# PRPs (Product Requirements Prompts)

This directory contains the "Blueprints" for all features implemented by Agents.

## Structure
- `templates/prp_base.md`: The template to copy.
- `<slug>.md`: Active feature plans.

## Workflow
1.  **Prime:** Agent reads context.
2.  **Generate:** Agent creates `PRPs/<slug>.md`.
3.  **Review:** User approves.
4.  **Execute:** Agent implements and checks off steps.
