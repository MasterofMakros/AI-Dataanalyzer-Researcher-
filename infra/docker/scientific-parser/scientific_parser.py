"""
Scientific Parser Service - FastAPI HTTP API
============================================

API für wissenschaftliche Tabular- und Text-Extraktion.

Endpoints:
- POST /extract - Datei hochladen und extrahieren
- POST /extract/path - Datei über Pfad extrahieren
- GET /supported - Unterstützte Formate
- GET /health - Health Check
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from scientific_extractors import (
    SUPPORTED_EXTENSIONS,
    TABULAR_EXTENSIONS,
    TEXT_EXTENSIONS,
    PDF_EXTENSIONS,
    ScientificExtractionError,
    extract_scientific_file,
)

app = FastAPI(
    title="Scientific Parser Service",
    description="Tabular- und Text-Extraktion für wissenschaftliche Formate",
    version="1.0.0",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "scientific-parser"}


@app.get("/supported")
async def supported() -> dict:
    return {
        "extensions": sorted(SUPPORTED_EXTENSIONS),
        "tabular": sorted(TABULAR_EXTENSIONS),
        "text": sorted(TEXT_EXTENSIONS),
        "pdf": sorted(PDF_EXTENSIONS),
    }


@app.post("/extract")
async def extract_file(file: UploadFile = File(...), extension: Optional[str] = None):
    if extension:
        suffix = extension if extension.startswith(".") else f".{extension}"
    else:
        suffix = Path(file.filename).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported extension: {suffix}")

    tmp_path = Path(f"/tmp/scientific-upload{suffix}")
    try:
        content = await file.read()
        tmp_path.write_bytes(content)
        payload = extract_scientific_file(tmp_path)
    except ScientificExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    return JSONResponse(content=payload)


@app.post("/extract/path")
async def extract_file_by_path(filepath: str):
    path = Path(filepath)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filepath}")

    try:
        payload = extract_scientific_file(path)
    except ScientificExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return JSONResponse(content=payload)


@app.get("/")
async def root():
    return {
        "service": "Scientific Parser Service",
        "version": "1.0.0",
        "endpoints": {
            "/health": "GET - Health Check",
            "/supported": "GET - Supported extensions",
            "/extract": "POST - Upload file for extraction",
            "/extract/path": "POST - Extract file by path",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8050)
