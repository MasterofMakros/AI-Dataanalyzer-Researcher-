@echo off
TITLE Conductor Worker Node (RTX 5090)
COLOR 0A

:: CONFIGURATION - Pi's LAN IP
set CONDUCTOR_API_URL=http://192.168.1.254:8000
set REDIS_HOST=192.168.1.254
set REDIS_PORT=6379

echo [INFO] Starting Worker Node...
echo [INFO] Target Conductor: %CONDUCTOR_API_URL%
echo [INFO] Anti-Sleep Protocol: ACTIVE

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.11+.
    pause
    exit /b
)

:: Install Dependencies
echo [INFO] Checking dependencies...
python -m pip install -r requirements.txt >nul 2>&1

:: Check FFmpeg
if not exist "..\bin\ffmpeg.exe" (
    echo [INFO] Installing FFmpeg...
    powershell -ExecutionPolicy Bypass -File "..\scripts\install_ffmpeg.ps1"
)
set PATH=%~dp0..\bin;%PATH%

:: Run the Worker
python worker.py

if %errorlevel% neq 0 (
    echo [ERROR] Worker crashed or stopped unexpectedly.
    pause
)
