# Context File Upgrade Tool - Simplified Version
# Enhances minimal _context.md files

$DriveRoot = "F:\"
$MinimalThreshold = 5

# Find all context files
Write-Host "=== CONTEXT FILE UPGRADE TOOL ===" -ForegroundColor Cyan
$contextFiles = Get-ChildItem $DriveRoot -Recurse -Filter "_context.md" -ErrorAction SilentlyContinue
Write-Host "Found $($contextFiles.Count) _context.md files" -ForegroundColor White
Write-Host ""

$upgraded = 0
$skipped = 0

foreach ($file in $contextFiles) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content) { $content = "" }
    $lineCount = ($content -split "`n").Count
    
    if ($lineCount -ge $MinimalThreshold) {
        Write-Host "[SKIP] $($file.FullName) ($lineCount lines)" -ForegroundColor Green
        $skipped = $skipped + 1
    }
    else {
        Write-Host ""
        Write-Host "[MINIMAL] $($file.FullName) ($lineCount lines)" -ForegroundColor Yellow
        Write-Host "Content: $content" -ForegroundColor DarkGray
        
        $folderName = Split-Path (Split-Path $file.FullName -Parent) -Leaf
        
        $newContent = @"
# Context: $folderName

## Purpose
$content

## Structure
*   [Unterordner hier auflisten]

## AI Instructions
*   Indexing: Standard
*   Priority: MEDIUM

## Search Tips
*   [Suchtipps hier einfuegen]
"@
        
        Write-Host "--- PROPOSED ---" -ForegroundColor Cyan
        Write-Host $newContent
        Write-Host "----------------" -ForegroundColor Cyan
        
        $response = Read-Host "Apply? (y/n/s=skip all)"
        
        if ($response -eq "s") { break }
        
        if ($response -eq "y") {
            Copy-Item $file.FullName "$($file.FullName).bak" -Force
            $newContent | Out-File $file.FullName -Encoding UTF8
            Write-Host "[UPGRADED]" -ForegroundColor Green
            $upgraded = $upgraded + 1
        }
        else {
            $skipped = $skipped + 1
        }
    }
}

Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "Upgraded: $upgraded | Skipped: $skipped"
