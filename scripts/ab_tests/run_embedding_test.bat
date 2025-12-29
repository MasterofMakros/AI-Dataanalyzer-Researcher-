@echo off
REM Neural Vault - A/B Test: Embedding Model Comparison
REM ====================================================

echo.
echo ============================================
echo Neural Vault A/B Test: Embedding Comparison
echo ============================================
echo.

REM Aktiviere conda/venv falls vorhanden
if exist "%~dp0..\..\venv\Scripts\activate.bat" (
    call "%~dp0..\..\venv\Scripts\activate.bat"
)

REM Wechsle ins Projekt-Root
cd /d "%~dp0..\.."

REM Prüfe Abhängigkeiten
echo Checking dependencies...
python -c "from sentence_transformers import SentenceTransformer; from sklearn.metrics import silhouette_score" 2>nul
if errorlevel 1 (
    echo.
    echo Missing dependencies! Installing...
    pip install sentence-transformers scikit-learn psutil
)

REM Führe Test durch
echo.
echo Starting A/B Test...
echo.

python scripts\ab_tests\embedding_comparison.py --samples 100

echo.
echo ============================================
echo Test completed! Check data\ab_tests\ for results.
echo ============================================

pause
