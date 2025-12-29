# PowerShell Style Guide

## 1. Naming Conventions
*   **Scripts**: `Verb-Noun_Description.ps1` (e.g., `Invoke-Migration_Phase1.ps1`).
*   **Variables**: CamelCase (e.g., `$TargetDirectory`, `$LogFile`).
*   **Functions**: `Verb-Noun` (Standard PowerShell verbs: Get, Set, New, Remove, Invoke).

## 2. Structure & Documentation
Every script must begin with a `SYNOPSIS` block:
```powershell
<#
.SYNOPSIS
    Short description of what the script does.
.DESCRIPTION
    Detailed explanation, including dependencies (Git, Robocopy).
.NOTES
    Author: Conductor AI
    Track: TRACK-XXX
#>
```

## 3. Error Handling
*   Use `try { ... } catch { ... }` blocks for file operations.
*   **Stop on Error**: `$ErrorActionPreference = "Stop"` for critical migration tasks.
*   **Log Everything**: Write critical errors to `$ManifestRepo\errors.log`.

## 4. Git Integration
*   Use the `Log-Manifest` function logic (from `migration_enterprise.ps1`) for all file moves/deletes.
*   Never use `rm` or `Del` without a prior hash check or git log.
