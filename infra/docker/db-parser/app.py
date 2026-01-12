"""
DB Parser Service - FastAPI HTTP API for database formats.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from db_parser import SUPPORTED_EXTENSIONS, build_schema, export_table

app = FastAPI(
    title="Neural Vault DB Parser Service",
    description="REST API for MDB/ACCDB/DBF/SQLite schema inspection and export",
    version="1.0.0",
)


def _normalize_extension(filename: str, extension: Optional[str]) -> str:
    if extension:
        ext = extension if extension.startswith(".") else f".{extension}"
    else:
        ext = Path(filename).suffix.lower()
    return ext.lower()


def _validate_extension(ext: str) -> None:
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported extension: {ext}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "db-parser"}


@app.get("/supported")
async def supported() -> dict:
    return {"extensions": sorted(SUPPORTED_EXTENSIONS), "count": len(SUPPORTED_EXTENSIONS)}


@app.post("/schema")
async def schema_from_upload(
    file: UploadFile = File(...),
    extension: Optional[str] = None,
    sample_rows: int = 5,
    include_row_counts: bool = True,
) -> JSONResponse:
    ext = _normalize_extension(file.filename, extension)
    _validate_extension(ext)

    content = await file.read()
    tmp_path = Path(f"/tmp/{file.filename}")
    tmp_path.write_bytes(content)
    try:
        schema = build_schema(tmp_path, sample_rows=sample_rows, include_row_counts=include_row_counts)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return JSONResponse(content=schema)


@app.post("/schema/path")
async def schema_from_path(
    filepath: str,
    sample_rows: int = 5,
    include_row_counts: bool = True,
) -> JSONResponse:
    path = Path(filepath)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
    _validate_extension(path.suffix.lower())
    schema = build_schema(path, sample_rows=sample_rows, include_row_counts=include_row_counts)
    return JSONResponse(content=schema)


@app.post("/export")
async def export_from_upload(
    file: UploadFile = File(...),
    table: str = "",
    output_format: str = "csv",
    limit: Optional[int] = None,
    extension: Optional[str] = None,
) -> PlainTextResponse:
    ext = _normalize_extension(file.filename, extension)
    _validate_extension(ext)
    if not table:
        raise HTTPException(status_code=400, detail="table is required")

    content = await file.read()
    tmp_path = Path(f"/tmp/{file.filename}")
    tmp_path.write_bytes(content)
    try:
        result = export_table(tmp_path, table=table, output_format=output_format, limit=limit)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return PlainTextResponse(content=result["content"])


@app.post("/export/path")
async def export_from_path(
    filepath: str,
    table: str,
    output_format: str = "csv",
    limit: Optional[int] = None,
) -> PlainTextResponse:
    path = Path(filepath)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
    _validate_extension(path.suffix.lower())
    result = export_table(path, table=table, output_format=output_format, limit=limit)
    return PlainTextResponse(content=result["content"])


@app.get("/")
async def root() -> dict:
    return {
        "service": "Neural Vault DB Parser Service",
        "version": "1.0.0",
        "endpoints": {
            "/health": "GET - Health Check",
            "/supported": "GET - Supported extensions",
            "/schema": "POST - Upload file for schema",
            "/schema/path": "POST - Schema by filepath",
            "/export": "POST - Export table from upload",
            "/export/path": "POST - Export table by filepath",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
