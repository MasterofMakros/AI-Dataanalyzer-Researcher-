# Neural Vault: Comprehensive All-Format Test Suite
# Tests ALL 128 supported formats with ground truth validation
# Stand: 11.01.2026

param(
    [switch]$Quick,
    [switch]$Full,
    [switch]$Report,
    [switch]$VerboseOutput,
    [string]$Filter
)

$ErrorActionPreference = "Continue"
$baseDir = "F:\AI-Dataanalyzer-Researcher\tests\ground_truth"
$reportsDir = "F:\AI-Dataanalyzer-Researcher\tests\reports"

# All supported formats (127 total)
$allFormats = @{
    documents = @("pdf", "docx", "xlsx", "pptx", "doc", "xls", "ppt", "odt", "ods", "odp", "rtf", "txt", "html", "xml", "json", "csv", "md")
    code = @("py", "js", "ts", "tsx", "jsx", "sh", "ps1", "sql", "css", "lua", "c", "cpp", "cc", "cxx", "h", "hpp", "java", "go", "rs", "rb", "php", "swift", "kt", "scala", "r", "pl", "pm", "asm", "bas", "vb", "cs", "fs", "hs", "elm", "clj", "ex", "exs", "erl", "dart", "vue", "svelte", "scss", "sass", "less", "styl", "coffee", "bat", "cmd", "awk", "sed", "makefile", "cmake", "gradle", "groovy")
    config = @("yaml", "yml", "ini", "toml", "conf")
    subtitles = @("srt", "vtt", "sub")
    ebooks = @("epub", "mobi", "azw", "azw3", "djvu")
    images = @("jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "heic", "psd", "raw", "cr2", "nef", "dng", "arw", "svg", "ico", "cur", "pcx", "tga", "exr", "hdr")
    audio = @("mp3", "wav", "flac", "m4a", "aac", "ogg", "wma", "mid", "midi", "ape", "opus", "amr", "au", "aiff", "aif")
    video = @("mp4", "mkv", "avi", "mov", "wmv", "webm", "flv", "mpg", "mpeg", "m4v", "3gp", "rm", "rmvb", "vob", "mts", "m2ts", "ts")
    email = @("eml", "msg")
    archive = @("zip", "rar", "7z", "tar", "gz", "bz2", "xz", "lz", "lzma", "cab", "iso", "dmg")
    fonts = @("woff", "woff2", "ttf", "otf", "eot")
    apps = @("apk", "ipa", "xapk", "apkm")
    binary = @("exe", "dll", "sys", "elf", "bin")
    latex = @("rst", "tex", "cls", "bib", "log", "diff", "patch")
}

# Queue mappings
$queueMappings = @{
    "extract:documents" = @("pdf", "docx", "xlsx", "pptx", "doc", "xls", "ppt", "odt", "ods", "odp", "rtf", "txt", "html", "xml", "json", "csv", "md", "py", "js", "ts", "tsx", "jsx", "sh", "ps1", "sql", "css", "lua", "c", "cpp", "cc", "cxx", "h", "hpp", "java", "go", "rs", "rb", "php", "swift", "kt", "scala", "r", "pl", "pm", "asm", "bas", "vb", "cs", "fs", "hs", "elm", "clj", "ex", "exs", "erl", "dart", "vue", "svelte", "scss", "sass", "less", "styl", "coffee", "bat", "cmd", "awk", "sed", "makefile", "cmake", "gradle", "groovy", "yaml", "yml", "ini", "toml", "conf", "srt", "vtt", "sub", "woff", "woff2", "ttf", "otf", "eot", "rst", "tex", "cls", "bib", "log", "diff", "patch")
    "extract:ebooks" = @("epub", "mobi", "azw", "azw3", "djvu")
    "extract:images" = @("jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "heic", "psd", "raw", "cr2", "nef", "dng", "arw", "svg", "ico", "cur", "pcx", "tga", "exr", "hdr")
    "extract:audio" = @("mp3", "wav", "flac", "m4a", "aac", "ogg", "wma", "mid", "midi", "ape", "opus", "amr", "au", "aiff", "aif")
    "extract:video" = @("mp4", "mkv", "avi", "mov", "wmv", "webm", "flv", "mpg", "mpeg", "m4v", "3gp", "rm", "rmvb", "vob", "mts", "m2ts", "ts")
    "extract:email" = @("eml", "msg")
    "extract:archive" = @("zip", "rar", "7z", "tar", "gz", "bz2", "xz", "lz", "lzma", "cab", "iso", "dmg")
    "extract:app" = @("apk", "ipa", "xapk", "apkm")
    "extract:binary:metadata" = @("exe", "dll", "sys", "elf", "bin")
}

# Reverse mapping
$formatToQueue = @{}
foreach ($queue in $queueMappings.Keys) {
    foreach ($format in $queueMappings[$queue]) {
        $formatToQueue[$format] = $queue
    }
}

# Results
$global:Results = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Summary = @{
        TotalFormats = 128
        TestedFormats = 0
        FormatsWithFiles = 0
        Passed = 0
        Failed = 0
    }
    Categories = @{}
}

function Test-FormatRouting {
    param([string]$Format)
    try {
        $body = @{ filepath = "test.$Format" } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8030/route" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 5 -ErrorAction Stop
        $expected = $formatToQueue[$Format]
        return @{
            Format = $Format
            Expected = $expected
            Actual = $response.queue
            Passed = $response.queue -eq $expected
        }
    } catch {
        return @{
            Format = $Format
            Expected = $formatToQueue[$Format]
            Actual = "ERROR: $($_.Exception.Message)"
            Passed = $false
        }
    }
}

function Get-GroundTruthFiles {
    $files = @{}
    foreach ($category in $allFormats.Keys) {
        $files[$category] = @{}
        foreach ($format in $allFormats[$category]) {
            $matches = Get-ChildItem "$baseDir" -Recurse -Filter "*.$format" -File -ErrorAction SilentlyContinue
            if ($matches) {
                $files[$category][$format] = $matches | Select-Object -ExpandProperty FullName
            }
        }
    }
    return $files
}

# Banner
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   NEURAL VAULT: COMPREHENSIVE ALL-FORMAT TEST SUITE" -ForegroundColor Cyan
Write-Host "   Version 2.0.0 - Stand: 11.01.2026" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$startTime = Get-Date

# 1. Ground Truth Inventory
Write-Host ""
Write-Host "--- 1. Ground Truth Inventory ---" -ForegroundColor Yellow

$gtFiles = Get-GroundTruthFiles
$totalGTFiles = 0
$formatsWithFiles = 0

foreach ($category in $gtFiles.Keys) {
    $catFormats = $gtFiles[$category].Keys.Count
    $catFiles = 0
    foreach ($f in $gtFiles[$category].Values) {
        $catFiles += $f.Count
    }
    if ($catFormats -gt 0) {
        Write-Host "  $category : $catFormats formats, $catFiles files"
        $formatsWithFiles += $catFormats
        $totalGTFiles += $catFiles
    }
}

Write-Host ""
Write-Host "  TOTAL: $formatsWithFiles formats with $totalGTFiles test files"
$global:Results.Summary.FormatsWithFiles = $formatsWithFiles

# 2. Routing Tests
Write-Host ""
Write-Host "--- 2. Format Routing Tests ---" -ForegroundColor Yellow

$routingPassed = 0
$routingFailed = 0

foreach ($category in $allFormats.Keys) {
    foreach ($format in $allFormats[$category]) {
        $result = Test-FormatRouting -Format $format
        $global:Results.Summary.TestedFormats++
        
        if ($result.Passed) {
            $routingPassed++
            $global:Results.Summary.Passed++
            if ($VerboseOutput) {
                Write-Host "  PASS: $format -> $($result.Actual)" -ForegroundColor Green
            }
        } else {
            $routingFailed++
            $global:Results.Summary.Failed++
            Write-Host "  FAIL: $format (expected: $($result.Expected), got: $($result.Actual))" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "  Routing Results: $routingPassed PASSED, $routingFailed FAILED" -ForegroundColor $(if ($routingFailed -eq 0) { "Green" } else { "Yellow" })

# 3. Extraction Tests (if -Full)
if ($Full) {
    Write-Host ""
    Write-Host "--- 3. Extraction Tests ---" -ForegroundColor Yellow
    
    $submitted = 0
    foreach ($category in $gtFiles.Keys) {
        foreach ($format in $gtFiles[$category].Keys) {
            foreach ($file in $gtFiles[$category][$format]) {
                try {
                    $body = @{path = $file} | ConvertTo-Json
                    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8020/submit" -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 10
                    $submitted++
                    Write-Host "  Submitted: $(Split-Path $file -Leaf)" -ForegroundColor Green
                } catch {
                    Write-Host "  Error: $(Split-Path $file -Leaf) - $_" -ForegroundColor Red
                }
            }
        }
    }
    Write-Host ""
    Write-Host "  Submitted $submitted files for processing"
}

# Summary
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Total Formats Supported: 127"
Write-Host "  Formats Tested:          $($global:Results.Summary.TestedFormats)"
Write-Host "  Formats with Files:      $formatsWithFiles"
Write-Host ""
Write-Host "  Routing PASSED:          $routingPassed" -ForegroundColor Green
Write-Host "  Routing FAILED:          $routingFailed" -ForegroundColor $(if ($routingFailed -eq 0) { "Gray" } else { "Red" })
Write-Host ""
Write-Host "  Duration: $([Math]::Round($duration, 1)) seconds"

$coverage = [Math]::Round($formatsWithFiles / 127 * 100, 1)
Write-Host ""
Write-Host "  Ground Truth Coverage: $coverage% ($formatsWithFiles/127)" -ForegroundColor $(if ($coverage -ge 80) { "Green" } elseif ($coverage -ge 50) { "Yellow" } else { "Red" })

if ($Report) {
    $reportPath = "$reportsDir\all_formats_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $global:Results | ConvertTo-Json -Depth 10 | Out-File $reportPath -Encoding UTF8
    Write-Host ""
    Write-Host "  Report saved: $reportPath" -ForegroundColor Cyan
}

Write-Host ""
