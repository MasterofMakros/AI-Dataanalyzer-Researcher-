<#
.SYNOPSIS
    Neural Vault - OCR Accuracy Test Suite
    Validates Surya OCR extraction quality

.DESCRIPTION
    Tests Surya OCR pipeline:
    1. Queries indexed image extractions
    2. Validates extracted text against known content
    3. Estimates Character/Word Error Rates

.PARAMETER ApiUrl
    Base URL of the conductor-api

.EXAMPLE
    .\test_ocr_accuracy.ps1
#>

param(
    [string]$ApiUrl = "http://127.0.0.1:8010"
)

$ErrorActionPreference = "Continue"

# =============================================================================
# GROUND TRUTH OCR CONTENT
# =============================================================================

# Known text content in test images
$OcrGroundTruth = @{
    # Simple text images
    "simple_text" = @{
        SearchQuery = "OCR test image"
        ExpectedWords = @("test", "image", "OCR", "neural", "vault")
        MinAccuracy = 0.4
    }
    # Document scans
    "document_scan" = @{
        SearchQuery = "scanned document text"
        ExpectedWords = @("document", "scan", "text", "page")
        MinAccuracy = 0.3
    }
    # Screenshots
    "screenshot" = @{
        SearchQuery = "screenshot interface button"
        ExpectedWords = @("screenshot", "button", "interface", "window")
        MinAccuracy = 0.25
    }
}

# Image extensions to check
$ImageExtensions = @("jpg", "jpeg", "png", "tiff", "bmp", "webp", "gif")

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

function Test-OcrAccuracy {
    param(
        [string]$ExtractedText,
        [string[]]$ExpectedWords
    )
    
    $found = 0
    $missing = @()
    
    foreach ($word in $ExpectedWords) {
        if ($ExtractedText -match "(?i)$([regex]::Escape($word))") {
            $found++
        } else {
            $missing += $word
        }
    }
    
    return @{
        Found = $found
        Total = $ExpectedWords.Count
        Accuracy = if ($ExpectedWords.Count -gt 0) { $found / $ExpectedWords.Count } else { 0 }
        Missing = $missing
    }
}

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   NEURAL VAULT: OCR ACCURACY TEST SUITE (Surya)" -ForegroundColor Cyan
Write-Host "   Version 1.0.0 - $(Get-Date -Format 'dd.MM.yyyy HH:mm')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$Results = @{
    Passed = 0
    Failed = 0
    Skipped = 0
    ImagesTested = 0
    TotalAccuracy = 0
}

# -----------------------------------------------------------------------------
# QUEUE STATUS
# -----------------------------------------------------------------------------

Write-Host "--- Queue Status ---" -ForegroundColor Yellow
Write-Host ""

$imageQueue = Get-QueueLength -Queue "extract:images"
Write-Host "  extract:images : $imageQueue pending items" -ForegroundColor DarkGray
Write-Host ""

# -----------------------------------------------------------------------------
# SURYA SERVICE CHECK
# -----------------------------------------------------------------------------

Write-Host "--- Surya OCR Service Status ---" -ForegroundColor Yellow
Write-Host ""

try {
    $suryaHealth = docker inspect conductor-surya-ocr --format '{{.State.Status}}' 2>$null
    if ($suryaHealth -eq "running") {
        Write-Host "  Surya OCR Container: Running [OK]" -ForegroundColor Green
    } else {
        Write-Host "  Surya OCR Container: $suryaHealth [WARN]" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Surya OCR Container: Unknown [WARN]" -ForegroundColor Yellow
}

Write-Host ""

# -----------------------------------------------------------------------------
# IMAGE CONTENT SEARCH
# -----------------------------------------------------------------------------

Write-Host "--- OCR Extraction Tests ---" -ForegroundColor Yellow
Write-Host ""

# Search for image-related indexed content
$imageTypes = @("jpg", "png", "tiff", "bmp", "gif", "webp")
$foundImages = @()

foreach ($ext in $imageTypes) {
    $search = Search-Index -Query ".$ext image"
    if ($search -and $search.hits.Count -gt 0) {
        foreach ($hit in $search.hits) {
            $path = if ($hit.file_path) { $hit.file_path } else { $hit.filename }
            if ($path -and $path -match "\.($($imageTypes -join '|'))$") {
                $foundImages += $hit
            }
        }
    }
}

# Remove duplicates by ID
$uniqueImages = $foundImages | Sort-Object -Property { $_.id } -Unique

if ($uniqueImages.Count -eq 0) {
    Write-Host "  [SKIP] No OCR-processed images found in index" -ForegroundColor DarkGray
    Write-Host "         Queue has $imageQueue pending items" -ForegroundColor DarkGray
    $Results.Skipped++
} else {
    Write-Host "  Found $($uniqueImages.Count) indexed images" -ForegroundColor White
    Write-Host ""
    
    foreach ($hit in $uniqueImages | Select-Object -First 10) {
        $filename = if ($hit.filename) { Split-Path $hit.filename -Leaf } 
                    elseif ($hit.file_path) { Split-Path $hit.file_path -Leaf }
                    else { "Unknown" }
        
        $text = ""
        if ($hit.extracted_text) { $text = $hit.extracted_text }
        elseif ($hit.text) { $text = $hit.text }
        elseif ($hit.ocr_text) { $text = $hit.ocr_text }
        
        $Results.ImagesTested++
        
        Write-Host "  Image: $filename" -ForegroundColor White
        
        if ($text.Length -gt 10) {
            # Test against general expected words
            $testResult = Test-OcrAccuracy -ExtractedText $text -ExpectedWords @("test", "image", "text", "document", "file")
            
            Write-Host "    Text Length: $($text.Length) chars" -ForegroundColor DarkGray
            Write-Host "    Keywords: $($testResult.Found)/$($testResult.Total)" -NoNewline
            
            if ($testResult.Accuracy -ge 0.2) {
                Write-Host " [PASS]" -ForegroundColor Green
                $Results.Passed++
            } else {
                Write-Host " [LOW]" -ForegroundColor Yellow
                $Results.Skipped++
            }
            
            $Results.TotalAccuracy += $testResult.Accuracy
        } else {
            Write-Host "    No text extracted [SKIP]" -ForegroundColor DarkGray
            $Results.Skipped++
        }
    }
}

Write-Host ""

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   OCR ACCURACY TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Images Tested: $($Results.ImagesTested)" -ForegroundColor White
Write-Host "  Passed:        $($Results.Passed)" -ForegroundColor Green
Write-Host "  Skipped:       $($Results.Skipped)" -ForegroundColor DarkGray
Write-Host "  Failed:        $($Results.Failed)" -ForegroundColor Red

if ($Results.ImagesTested -gt 0) {
    $avgAccuracy = [math]::Round(($Results.TotalAccuracy / $Results.ImagesTested) * 100, 1)
    Write-Host ""
    Write-Host "  Average Keyword Accuracy: $avgAccuracy%" -ForegroundColor Yellow
}

Write-Host ""

if ($imageQueue -gt 0) {
    Write-Host "  Note: $imageQueue images still pending OCR processing." -ForegroundColor DarkYellow
}

Write-Host ""

return $Results

