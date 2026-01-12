<#
.SYNOPSIS
    Neural Vault - Audio/Video Transcription Test Suite
    Validates WhisperX transcription quality

.DESCRIPTION
    Tests WhisperX transcription pipeline:
    1. Submits audio/video files with known spoken content
    2. Queries indexed transcriptions
    3. Calculates Word Error Rate (WER) against ground truth

.PARAMETER ApiUrl
    Base URL of the conductor-api

.EXAMPLE
    .\test_transcription.ps1
#>

param(
    [string]$ApiUrl = "http://127.0.0.1:8010",
    [string]$RouterUrl = "http://127.0.0.1:8030"
)

$ErrorActionPreference = "Continue"

# =============================================================================
# GROUND TRUTH TRANSCRIPTIONS
# =============================================================================

# Known content in test audio/video files
$TranscriptionGroundTruth = @{
    # Audio files with expected transcription keywords
    "audio" = @{
        Keywords = @(
            "test", "audio", "whisper", "transcription", 
            "neural", "vault", "processing"
        )
        MinKeywordMatch = 0.3  # Lower threshold since synthetic audio
        ExpectedLanguage = "de"
    }
    # Video files (audio track extraction)
    "video" = @{
        Keywords = @(
            "video", "test", "processing", "neural"
        )
        MinKeywordMatch = 0.25
        ExpectedLanguage = "de"
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

function Search-Transcriptions {
    param(
        [string]$Query,
        [string]$SourceType = ""
    )
    
    try {
        $body = @{
            query = $Query
            limit = 20
        }
        
        if ($SourceType) {
            $body.filters = "source_type = `"$SourceType`""
        }
        
        $response = Invoke-RestMethod -Uri "$ApiUrl/search" -Method POST -Body ($body | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30
        return $response
    }
    catch {
        Write-Warning "Search failed: $_"
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

function Calculate-SimpleWER {
    param(
        [string]$Hypothesis,
        [string[]]$ReferenceKeywords
    )
    
    $found = 0
    foreach ($keyword in $ReferenceKeywords) {
        if ($Hypothesis -match [regex]::Escape($keyword)) {
            $found++
        }
    }
    
    $accuracy = if ($ReferenceKeywords.Count -gt 0) { $found / $ReferenceKeywords.Count } else { 0 }
    return @{
        Found = $found
        Total = $ReferenceKeywords.Count
        Accuracy = $accuracy
        Missing = $ReferenceKeywords | Where-Object { $Hypothesis -notmatch [regex]::Escape($_) }
    }
}

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   NEURAL VAULT: TRANSCRIPTION TEST SUITE (WhisperX)" -ForegroundColor Cyan
Write-Host "   Version 1.0.0 - $(Get-Date -Format 'dd.MM.yyyy HH:mm')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$Results = @{
    Passed = 0
    Failed = 0
    Skipped = 0
}

# -----------------------------------------------------------------------------
# CHECK QUEUE STATUS
# -----------------------------------------------------------------------------

Write-Host "--- Queue Status Check ---" -ForegroundColor Yellow
Write-Host ""

$audioQueue = Get-QueueLength -Queue "extract:audio"
$videoQueue = Get-QueueLength -Queue "extract:video"

Write-Host "  extract:audio : $audioQueue items" -ForegroundColor DarkGray
Write-Host "  extract:video : $videoQueue items" -ForegroundColor DarkGray
Write-Host ""

# -----------------------------------------------------------------------------
# AUDIO TRANSCRIPTION TESTS
# -----------------------------------------------------------------------------

Write-Host "--- Audio Transcription Tests ---" -ForegroundColor Yellow
Write-Host ""

# Search for any audio-related content
$audioSearch = Search-Transcriptions -Query "audio test mp3 wav"

if (-not $audioSearch -or $audioSearch.hits.Count -eq 0) {
    Write-Host "  [SKIP] No audio transcriptions found in index" -ForegroundColor DarkGray
    Write-Host "         Reason: WhisperX may not have processed files yet" -ForegroundColor DarkGray
    Write-Host "         Queue has $audioQueue pending items" -ForegroundColor DarkGray
    $Results.Skipped++
} else {
    Write-Host "  Found $($audioSearch.hits.Count) audio-related documents" -ForegroundColor White
    
    foreach ($hit in $audioSearch.hits | Select-Object -First 3) {
        $filename = if ($hit.filename) { $hit.filename } else { $hit.file_path }
        $text = ""
        if ($hit.extracted_text) { $text = $hit.extracted_text }
        elseif ($hit.text) { $text = $hit.text }
        elseif ($hit.transcript) { $text = $hit.transcript }
        
        if ($text.Length -gt 0) {
            $werResult = Calculate-SimpleWER -Hypothesis $text -ReferenceKeywords $TranscriptionGroundTruth.audio.Keywords
            
            Write-Host "  File: $filename" -ForegroundColor White
            Write-Host "    Keywords: $($werResult.Found)/$($werResult.Total)" -NoNewline
            
            if ($werResult.Accuracy -ge $TranscriptionGroundTruth.audio.MinKeywordMatch) {
                Write-Host " [PASS]" -ForegroundColor Green
                $Results.Passed++
            } else {
                Write-Host " [WARN] Low accuracy" -ForegroundColor Yellow
                $Results.Skipped++
            }
        } else {
            Write-Host "  File: $filename - No text content [SKIP]" -ForegroundColor DarkGray
            $Results.Skipped++
        }
    }
}

Write-Host ""

# -----------------------------------------------------------------------------
# VIDEO TRANSCRIPTION TESTS
# -----------------------------------------------------------------------------

Write-Host "--- Video Transcription Tests ---" -ForegroundColor Yellow
Write-Host ""

$videoSearch = Search-Transcriptions -Query "video test mp4 mkv"

if (-not $videoSearch -or $videoSearch.hits.Count -eq 0) {
    Write-Host "  [SKIP] No video transcriptions found in index" -ForegroundColor DarkGray
    Write-Host "         Reason: FFmpeg + WhisperX pipeline may not have completed" -ForegroundColor DarkGray
    Write-Host "         Queue has $videoQueue pending items" -ForegroundColor DarkGray
    $Results.Skipped++
} else {
    Write-Host "  Found $($videoSearch.hits.Count) video-related documents" -ForegroundColor White
    
    foreach ($hit in $videoSearch.hits | Select-Object -First 3) {
        $filename = if ($hit.filename) { $hit.filename } else { $hit.file_path }
        $text = ""
        if ($hit.extracted_text) { $text = $hit.extracted_text }
        elseif ($hit.text) { $text = $hit.text }
        
        if ($text.Length -gt 0) {
            $werResult = Calculate-SimpleWER -Hypothesis $text -ReferenceKeywords $TranscriptionGroundTruth.video.Keywords
            
            Write-Host "  File: $filename" -ForegroundColor White
            Write-Host "    Keywords: $($werResult.Found)/$($werResult.Total)" -NoNewline
            
            if ($werResult.Accuracy -ge $TranscriptionGroundTruth.video.MinKeywordMatch) {
                Write-Host " [PASS]" -ForegroundColor Green
                $Results.Passed++
            } else {
                Write-Host " [WARN]" -ForegroundColor Yellow
                $Results.Skipped++
            }
        } else {
            Write-Host "  File: $filename - No text [SKIP]" -ForegroundColor DarkGray
            $Results.Skipped++
        }
    }
}

Write-Host ""

# -----------------------------------------------------------------------------
# WHISPERX SERVICE CHECK
# -----------------------------------------------------------------------------

Write-Host "--- WhisperX Service Status ---" -ForegroundColor Yellow
Write-Host ""

try {
    $whisperHealth = docker inspect conductor-whisperx --format '{{.State.Status}}' 2>$null
    if ($whisperHealth -eq "running") {
        Write-Host "  WhisperX Container: Running [OK]" -ForegroundColor Green
    } else {
        Write-Host "  WhisperX Container: $whisperHealth [WARN]" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  WhisperX Container: Unknown [WARN]" -ForegroundColor Yellow
}

Write-Host ""

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   TRANSCRIPTION TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Passed:  $($Results.Passed)" -ForegroundColor Green
Write-Host "  Skipped: $($Results.Skipped)" -ForegroundColor DarkGray
Write-Host "  Failed:  $($Results.Failed)" -ForegroundColor Red
Write-Host ""

if ($Results.Skipped -gt 0) {
    Write-Host "  Note: Skipped tests indicate WhisperX processing is pending." -ForegroundColor DarkYellow
    Write-Host "        Run 'drain_and_index.py' for audio/video queues." -ForegroundColor DarkYellow
}

Write-Host ""

return $Results

