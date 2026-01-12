"""
Special Parser Service
======================

HTTP API für Spezialformate.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from special_parser_core import PARSERS, parse_file


class ParseRequest(BaseModel):
    filepath: str
    category: Optional[str] = None


app = FastAPI(
    title="Special Parser Service",
    description="Parser für 3D, CAD, GIS und Fonts",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "special-parser"}


@app.get("/supported")
async def supported():
    return {
        "categories": {
            parser.category: parser.extensions
            for parser in PARSERS
        }
    }


@app.post("/parse")
async def parse_upload(file: UploadFile = File(...), category: Optional[str] = None):
    ext = Path(file.filename).suffix.lower()
    if not ext:
        raise HTTPException(status_code=400, detail="File extension missing")

    tmp_path = Path("/tmp") / f"special-parser-{file.filename}"
    content = await file.read()
    tmp_path.write_bytes(content)

    try:
        result = parse_file(tmp_path, category)
        result.filename = file.filename
        result.filepath = file.filename
        return asdict(result)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@app.post("/parse/path")
async def parse_path(request: ParseRequest):
    path = Path(request.filepath)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    result = parse_file(path, request.category)
    return asdict(result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8015)
