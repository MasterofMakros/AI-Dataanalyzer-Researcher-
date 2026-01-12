"""
Neural Vault Metadata Extractor Service
======================================

Exiftool-basierter Metadata-Service für RAW, PSD, EXE, AI, XCF, ICO, etc.

Endpoints:
- GET /health
- GET /supported
- POST /metadata (file upload)
- POST /metadata/path (extract by path on /mnt/data)
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import subprocess


EXIFTOOL_BIN = os.getenv("EXIFTOOL_BIN", "exiftool")
EXIFTOOL_TIMEOUT = int(os.getenv("EXIFTOOL_TIMEOUT", "30"))

SUPPORTED_EXTENSIONS = sorted({
    ".ai",
    ".arw",
    ".cr2",
    ".cr3",
    ".dng",
    ".exe",
    ".ico",
    ".nef",
    ".orf",
    ".pef",
    ".psd",
    ".raf",
    ".raw",
    ".rw2",
    ".xcf",
})


class PathRequest(BaseModel):
    filepath: str
    include_binary: bool = False


app = FastAPI(
    title="Neural Vault Metadata Extractor",
    description="Exiftool-powered metadata extraction API",
    version="1.0.0"
)


def _run_exiftool(filepath: Path, include_binary: bool) -> Dict[str, Any]:
    args = [
        EXIFTOOL_BIN,
        "-json",
        "-G",
        "-a",
        "-u",
        "-n",
    ]

    if include_binary:
        args.append("-b")

    args.append(str(filepath))

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=EXIFTOOL_TIMEOUT
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Exiftool error: {result.stderr.strip() or 'unknown error'}"
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid JSON from exiftool: {exc}")

    if not payload:
        return {}

    metadata = payload[0]
    metadata["extracted_via"] = "exiftool"
    metadata["exiftool_version"] = get_exiftool_version()

    return metadata


def get_exiftool_version() -> str:
    try:
        result = subprocess.run(
            [EXIFTOOL_BIN, "-ver"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return "unknown"


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy", "service": "metadata-extractor"}


@app.get("/supported")
async def supported_extensions() -> Dict[str, Any]:
    return {"extensions": SUPPORTED_EXTENSIONS, "count": len(SUPPORTED_EXTENSIONS)}


@app.post("/metadata")
async def metadata_upload(
    file: UploadFile = File(...),
    include_binary: bool = False
) -> JSONResponse:
    suffix = Path(file.filename).suffix.lower() or ".bin"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        metadata = _run_exiftool(tmp_path, include_binary)
        metadata["original_filename"] = file.filename
        return JSONResponse(content=metadata)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@app.post("/metadata/path")
async def metadata_by_path(request: PathRequest) -> JSONResponse:
    path = Path(request.filepath)

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.filepath}")

    metadata = _run_exiftool(path, request.include_binary)
    metadata["original_filepath"] = request.filepath
    return JSONResponse(content=metadata)


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "service": "Neural Vault Metadata Extractor",
        "version": "1.0.0",
        "endpoints": {
            "/health": "GET - Health Check",
            "/supported": "GET - Supported extensions",
            "/metadata": "POST - Upload file",
            "/metadata/path": "POST - Extract by file path"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
