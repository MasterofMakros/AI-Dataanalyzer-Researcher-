"""
Neural Vault Parser Service - FastAPI HTTP API
===============================================

Docker-basierter Datei-Parser Service.
Ersetzt lokale Python-Bibliotheken durch HTTP API.

Endpoints:
- POST /parse - Datei parsen
- GET /health - Health Check
- GET /supported - Unterstützte Erweiterungen
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

# Parser importieren
from extended_file_processor import (
    process_extended_file,
    get_supported_extensions,
    is_extended_processable,
    ExtendedProcessingResult
)
from dataclasses import asdict

app = FastAPI(
    title="Neural Vault Parser Service",
    description="Docker-basierter Datei-Parser für erweiterte Dateitypen",
    version="1.0.0"
)


@app.get("/health")
async def health():
    """Health Check Endpoint."""
    return {"status": "healthy", "service": "parser-service"}


@app.get("/supported")
async def supported_extensions():
    """Liste der unterstützten Datei-Erweiterungen."""
    extensions = get_supported_extensions()
    return {
        "extensions": extensions,
        "count": len(extensions)
    }


@app.post("/parse")
async def parse_file(
    file: UploadFile = File(...),
    extension: Optional[str] = None
):
    """
    Parse eine hochgeladene Datei.
    
    Args:
        file: Die zu parsende Datei
        extension: Optional - Dateiendung überschreiben
    
    Returns:
        ExtendedProcessingResult als JSON
    """
    # Bestimme Dateiendung
    if extension:
        ext = extension if extension.startswith(".") else f".{extension}"
    else:
        ext = Path(file.filename).suffix.lower()
    
    # Prüfe ob unterstützt
    supported = get_supported_extensions()
    if ext not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Nicht unterstützte Dateiendung: {ext}. Unterstützt: {', '.join(supported)}"
        )
    
    # Temporäre Datei erstellen
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        # Datei verarbeiten
        result = process_extended_file(tmp_path)
        
        # Originalname in Result setzen
        result.filename = file.filename
        result.filepath = file.filename
        
        return JSONResponse(content=asdict(result))
        
    finally:
        # Temporäre Datei löschen
        if tmp_path.exists():
            tmp_path.unlink()


@app.post("/parse/path")
async def parse_file_by_path(filepath: str):
    """
    Parse eine Datei über ihren Pfad (für Container-Volumes).
    
    Args:
        filepath: Pfad zur Datei im Container (z.B. /mnt/data/file.torrent)
    
    Returns:
        ExtendedProcessingResult als JSON
    """
    path = Path(filepath)
    
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Datei nicht gefunden: {filepath}"
        )
    
    ext = path.suffix.lower()
    supported = get_supported_extensions()
    
    if ext not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Nicht unterstützte Dateiendung: {ext}"
        )
    
    result = process_extended_file(path)
    return JSONResponse(content=asdict(result))


@app.get("/")
async def root():
    """API Root - Zeigt verfügbare Endpoints."""
    return {
        "service": "Neural Vault Parser Service",
        "version": "1.0.0",
        "endpoints": {
            "/health": "GET - Health Check",
            "/supported": "GET - Unterstützte Erweiterungen",
            "/parse": "POST - Datei hochladen und parsen",
            "/parse/path": "POST - Datei über Pfad parsen"
        },
        "supported_extensions": get_supported_extensions()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
