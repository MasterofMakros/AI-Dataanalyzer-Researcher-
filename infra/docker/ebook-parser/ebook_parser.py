"""
Neural Vault Ebook Parser Service
=================================

API für das Extrahieren von Text und Metadaten aus E-Books.
Unterstützte Formate: EPUB, MOBI, AZW, AZW3, DjVu.
"""

import os
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from ebooklib import epub
from bs4 import BeautifulSoup

SUPPORTED_EXTENSIONS = {".epub", ".mobi", ".azw", ".azw3", ".djvu", ".djv"}

app = FastAPI(
    title="Neural Vault Ebook Parser",
    description="Extrahiert Text und Metadaten aus E-Books",
    version="1.0.0",
)


def _clean_text(chunks: List[str]) -> str:
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def _parse_epub(path: Path) -> Dict[str, Any]:
    book = epub.read_epub(str(path))
    text_chunks: List[str] = []

    for item in book.get_items_of_type(epub.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "lxml")
        text_chunks.append(soup.get_text(" ", strip=True))

    metadata: Dict[str, Any] = {
        "title": _first_metadata(book, "title"),
        "creators": _metadata_list(book, "creator"),
        "language": _first_metadata(book, "language"),
        "publisher": _first_metadata(book, "publisher"),
        "format": "epub",
    }

    return {
        "text": _clean_text(text_chunks),
        "metadata": metadata,
        "extraction_method": "ebooklib-epub",
    }


def _parse_kindle(path: Path) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "unpacked"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            ["kindleunpack", str(path), str(output_dir)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"KindleUnpack failed: {result.stderr.strip()}")

        html_files = sorted(
            list(output_dir.rglob("*.html"))
            + list(output_dir.rglob("*.xhtml"))
            + list(output_dir.rglob("*.htm"))
        )

        text_chunks: List[str] = []
        for html_file in html_files:
            soup = BeautifulSoup(html_file.read_text(encoding="utf-8", errors="ignore"), "lxml")
            text_chunks.append(soup.get_text(" ", strip=True))

        metadata = _parse_opf_metadata(output_dir)
        metadata["format"] = path.suffix.lower().lstrip(".")

        return {
            "text": _clean_text(text_chunks),
            "metadata": metadata,
            "extraction_method": "kindleunpack",
        }


def _parse_opf_metadata(output_dir: Path) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {}
    opf_files = list(output_dir.rglob("*.opf"))
    if not opf_files:
        return metadata

    opf_path = opf_files[0]
    soup = BeautifulSoup(opf_path.read_text(encoding="utf-8", errors="ignore"), "xml")

    def get_text(tag: str) -> Optional[str]:
        element = soup.find(tag)
        return element.text.strip() if element and element.text else None

    creators = [creator.text.strip() for creator in soup.find_all("dc:creator") if creator.text]

    metadata.update(
        {
            "title": get_text("dc:title"),
            "creators": creators,
            "language": get_text("dc:language"),
            "publisher": get_text("dc:publisher"),
        }
    )

    return {k: v for k, v in metadata.items() if v}


def _parse_djvu(path: Path) -> Dict[str, Any]:
    result = subprocess.run(
        ["djvutxt", str(path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"djvutxt failed: {result.stderr.strip()}")

    metadata: Dict[str, Any] = {"format": "djvu"}

    pages = _djvu_page_count(path)
    if pages is not None:
        metadata["pages"] = pages

    return {
        "text": result.stdout.strip(),
        "metadata": metadata,
        "extraction_method": "djvutxt",
    }


def _djvu_page_count(path: Path) -> Optional[int]:
    result = subprocess.run(
        ["djvused", str(path), "-e", "n"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def _first_metadata(book: epub.EpubBook, name: str) -> Optional[str]:
    values = book.get_metadata("DC", name)
    if not values:
        return None
    value = values[0][0]
    return value.strip() if isinstance(value, str) else None


def _metadata_list(book: epub.EpubBook, name: str) -> List[str]:
    values = book.get_metadata("DC", name)
    return [val[0].strip() for val in values if isinstance(val[0], str)]


def parse_ebook(path: Path) -> Dict[str, Any]:
    ext = path.suffix.lower()
    if ext == ".epub":
        return _parse_epub(path)
    if ext in {".mobi", ".azw", ".azw3"}:
        return _parse_kindle(path)
    if ext in {".djvu", ".djv"}:
        return _parse_djvu(path)

    raise ValueError(f"Unsupported ebook format: {ext}")


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy", "service": "ebook-parser"}


@app.get("/supported")
async def supported_extensions() -> Dict[str, Any]:
    return {"extensions": sorted(SUPPORTED_EXTENSIONS), "count": len(SUPPORTED_EXTENSIONS)}


@app.post("/extract")
async def extract_file(file: UploadFile = File(...), extension: Optional[str] = None):
    ext = extension or Path(file.filename).suffix.lower()

    if not ext.startswith("."):
        ext = f".{ext}"

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported extension: {ext}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = parse_ebook(tmp_path)
        response = {
            "filename": file.filename,
            "extension": ext,
            **result,
        }
        return JSONResponse(content=response)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@app.post("/extract/path")
async def extract_file_by_path(filepath: str):
    path = Path(filepath)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filepath}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported extension: {path.suffix}")

    result = parse_ebook(path)
    return JSONResponse(content={"filename": path.name, "extension": path.suffix.lower(), **result})


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "service": "Neural Vault Ebook Parser",
        "version": "1.0.0",
        "endpoints": {
            "/health": "GET - Health Check",
            "/supported": "GET - Supported extensions",
            "/extract": "POST - Upload and extract",
            "/extract/path": "POST - Extract by path",
        },
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
