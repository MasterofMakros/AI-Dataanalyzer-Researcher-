$ErrorActionPreference = "Stop"
$ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$destDir = "F:\conductor\bin"
$zipPath = "$destDir\ffmpeg.zip"

if (Test-Path "$destDir\ffmpeg.exe") {
    Write-Host "FFmpeg already installed."
    exit 0
}

Write-Host "Creating bin directory..."
New-Item -ItemType Directory -Force -Path $destDir | Out-Null

Write-Host "Downloading FFmpeg (this may take a minute)..."
Invoke-WebRequest -Uri $ffmpegUrl -OutFile $zipPath

Write-Host "Extracting..."
Expand-Archive -Path $zipPath -DestinationPath $destDir -Force

Write-Host "Locating binaries..."
$extractedRoot = Get-ChildItem -Path $destDir -Directory | Select-Object -First 1
$binFolder = Join-Path $extractedRoot.FullName "bin"

Move-Item -Path "$binFolder\*" -Destination $destDir -Force
Remove-Item -Path $extractedRoot.FullName -Recurse -Force
Remove-Item -Path $zipPath -Force

Write-Host "FFmpeg installed to $destDir"
