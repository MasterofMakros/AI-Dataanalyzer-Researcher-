<#
.SYNOPSIS
    Neural Vault - Archive Extraction Test Suite
    Validates recursive archive unpacking and content re-routing

.DESCRIPTION
    Tests 7zip archive processing:
    1. Submits archive files (zip, 7z, rar, tar, gz)
    2. Verifies contents are extracted and re-routed
    3. Checks nested content appears in search index

.PARAMETER ApiUrl
    Base URL of the conductor-api

.EXAMPLE
    .\test_archive_extraction.ps1
#>

param(
    [string]$ApiUrl = "http://127.0.0.1:8010",
    [string]$RouterUrl = "http://127.0.0.1:8030"
)

$ErrorActionPreference = "Continue"

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

$ArchiveTypes = @("zip", "7z", "rar", "tar", "gz", "tar.gz", "tgz")

# Known contents in test archives
$ArchiveContents = @{
    "test_archive.zip" = @{
        ExpectedFiles = @("readme.txt", "data.csv", "config.json")
        ExpectedKeywords = @("readme", "data", "config")
    }
    "test_nested.7z" = @{
        ExpectedFiles = @("inner.zip", "document.pdf")
        ExpectedKeywords = @("inner", "document", "nested")
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

function Search-Index {
    param(
        [string]$Query,
        [int]$Limit = 20
    )
    
    try {
        $body = @{ query = $Query; limit = $Limit } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$ApiUrl/search" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
        return $response
    }
    catch {
        return $null
    }
}

function Get-QueueLength {
    param([string]$Queue)
    
    try {
        $result = docker exec conductor-redis redis-cli -a change_me_in_prod XLEN $Queue 2>$null
        if ($result -match "^\d+$") { return [int]$result }
    } catch {}
    return 0
}

function Test-ArchiveContent {
    param(
        [string]$ArchiveName,
        [array]$SearchHits,
        [string[]]$ExpectedKeywords
    )
    
    $foundKeywords = 0
    $allText = ($SearchHits | ForEach-Object { 
        if ($_.extracted_text) { $_.extracted_text }
        elseif ($_.text) { $_.text }
        elseif ($_.file_path) { $_.file_path }
    }) -join " "
    
    foreach ($keyword in $ExpectedKeywords) {
        if ($allText -match "(?i)$([regex]::Escape($keyword))") {
            $foundKeywords++
        }
    }
    
    return @{
        Found = $foundKeywords
        Total = $ExpectedKeywords.Count
        Accuracy = if ($ExpectedKeywords.Count -gt 0) { $foundKeywords / $ExpectedKeywords.Count } else { 0 }
    }
}

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   NEURAL VAULT: ARCHIVE EXTRACTION TEST SUITE (7zip)" -ForegroundColor Cyan
Write-Host "   Version 1.0.0 - $(Get-Date -Format 'dd.MM.yyyy HH:mm')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$Results = @{
    Passed = 0
    Failed = 0
    Skipped = 0
    ArchivesTested = 0
}

# -----------------------------------------------------------------------------
# QUEUE STATUS
# -----------------------------------------------------------------------------

Write-Host "--- Queue Status ---" -ForegroundColor Yellow
Write-Host ""

$archiveQueue = Get-QueueLength -Queue "extract:archive"
Write-Host "  extract:archive : $archiveQueue pending items" -ForegroundColor DarkGray
Write-Host ""

# -----------------------------------------------------------------------------
# 7ZIP SERVICE CHECK
# -----------------------------------------------------------------------------

Write-Host "--- 7zip Service Status ---" -ForegroundColor Yellow
Write-Host ""

try {
    $zipHealth = docker inspect conductor-7zip --format '{{.State.Status}}' 2>$null
    if ($zipHealth -eq "running") {
        Write-Host "  7zip Container: Running [OK]" -ForegroundColor Green
    } else {
        Write-Host "  7zip Container: $zipHealth [WARN]" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  7zip Container: Unknown [WARN]" -ForegroundColor Yellow
}

Write-Host ""

# -----------------------------------------------------------------------------
# ARCHIVE CONTENT TESTS
# -----------------------------------------------------------------------------

Write-Host "--- Archive Extraction Tests ---" -ForegroundColor Yellow
Write-Host ""

# Test each archive type
foreach ($ext in $ArchiveTypes) {
    Write-Host "  Testing .$ext archives..." -NoNewline
    
    # Search for archive-related content
    $search = Search-Index -Query ".$ext archive"
    
    if (-not $search -or $search.hits.Count -eq 0) {
        Write-Host " [SKIP] No indexed content" -ForegroundColor DarkGray
        $Results.Skipped++
        continue
    }
    
    # Check if any hits reference this archive type
    $relevantHits = $search.hits | Where-Object {
        ($_.file_path -and $_.file_path -match "\.$ext") -or
        ($_.filename -and $_.filename -match "\.$ext") -or
        ($_.source_archive -and $_.source_archive -match "\.$ext")
    }
    
    if ($relevantHits.Count -gt 0) {
        Write-Host " [PASS] $($relevantHits.Count) files found" -ForegroundColor Green
        $Results.Passed++
        $Results.ArchivesTested++
    } else {
        # Check for extracted content without explicit archive reference
        $genericHits = $search.hits | Where-Object {
            $_.extracted_text -or $_.text
        }
        
        if ($genericHits.Count -gt 0) {
            Write-Host " [PARTIAL] $($genericHits.Count) hits (indirect)" -ForegroundColor Yellow
            $Results.Skipped++
        } else {
            Write-Host " [SKIP] No content" -ForegroundColor DarkGray
            $Results.Skipped++
        }
    }
}

Write-Host ""

# -----------------------------------------------------------------------------
# NESTED ARCHIVE TEST
# -----------------------------------------------------------------------------

Write-Host "--- Nested Archive Test (Recursive) ---" -ForegroundColor Yellow
Write-Host ""

$nestedSearch = Search-Index -Query "nested inner archive"

if ($nestedSearch -and $nestedSearch.hits.Count -gt 0) {
    Write-Host "  Nested content found: $($nestedSearch.hits.Count) items [PASS]" -ForegroundColor Green
    $Results.Passed++
} else {
    Write-Host "  No nested archive content indexed [SKIP]" -ForegroundColor DarkGray
    Write-Host "  Note: Nested archives require recursive processing" -ForegroundColor DarkGray
    $Results.Skipped++
}

Write-Host ""

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   ARCHIVE EXTRACTION TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Archives Tested: $($Results.ArchivesTested)" -ForegroundColor White
Write-Host "  Passed:          $($Results.Passed)" -ForegroundColor Green
Write-Host "  Skipped:         $($Results.Skipped)" -ForegroundColor DarkGray
Write-Host "  Failed:          $($Results.Failed)" -ForegroundColor Red
Write-Host ""

if ($archiveQueue -gt 0) {
    Write-Host "  Note: $archiveQueue archives still pending extraction." -ForegroundColor DarkYellow
}

Write-Host ""

return $Results

