# Examples & Patterns

This directory contains reference implementations for common patterns in this repository.
**Agents must treat these as the "Gold Standard" for implementation style.**

## Available Patterns

| File | Pattern Type | Description |
| :--- | :--- | :--- |
| `cli_pattern.ps1` | PowerShell CLI | Argument parsing, error handling, output coloring. |
| `service_pattern.py` | FastAPI Service | standard service structure, config, health checks. |

## How to Use
1.  **Read** the relevant pattern file.
2.  **Copy** the structure (imports, class layout, error handling block).
3.  **Adapt** logical internals to your specific feature.

## Do's and Don'ts
*   **DO** use Pydantic for data validation in Python.
*   **DO** use `Write-Host` with colors in PowerShell for user feedback.
*   **DON'T** hardcode secrets (use `os.getenv` or `$env:`).
*   **DON'T** swallow exceptions without logging.
