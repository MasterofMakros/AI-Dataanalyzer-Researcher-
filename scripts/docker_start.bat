@echo off
REM =============================================================================
REM Neural Vault Docker Startup Script (Windows)
REM =============================================================================
REM Usage:
REM   docker_start.bat              - Start all services
REM   docker_start.bat api          - Start only API and dependencies
REM   docker_start.bat rebuild      - Rebuild and start
REM   docker_start.bat logs         - Show logs
REM   docker_start.bat stop         - Stop all services
REM =============================================================================

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

set CORE_SERVICES=redis tika qdrant
set API_SERVICES=%CORE_SERVICES% conductor-api

if "%1"=="" goto all
if "%1"=="all" goto all
if "%1"=="api" goto api
if "%1"=="rebuild" goto rebuild
if "%1"=="logs" goto logs
if "%1"=="stop" goto stop
if "%1"=="status" goto status
goto usage

:all
echo [%time%] Starte alle Services...
docker compose up -d
echo [%time%] Alle Services gestartet
docker compose ps
goto end

:api
echo [%time%] Starte API-Services...
docker compose up -d %API_SERVICES%
echo [%time%] Warte auf Services...
timeout /t 10 /nobreak > nul
echo [%time%] API verfuegbar unter: http://localhost:8010
echo [%time%] API Docs: http://localhost:8010/docs
goto end

:rebuild
echo [%time%] Rebuild conductor-api...
docker compose build conductor-api
docker compose up -d conductor-api
echo [%time%] Rebuild abgeschlossen
goto end

:logs
if "%2"=="" (
    docker compose logs -f conductor-api
) else (
    docker compose logs -f %2
)
goto end

:stop
echo [%time%] Stoppe alle Services...
docker compose down
echo [%time%] Gestoppt
goto end

:status
docker compose ps
goto end

:usage
echo Usage: %0 {api^|rebuild^|logs^|stop^|status^|all}
goto end

:end
endlocal
