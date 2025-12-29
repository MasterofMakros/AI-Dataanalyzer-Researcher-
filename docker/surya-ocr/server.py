"""
Surya OCR API Server
====================

Hochpräzise OCR mit Layout-Analyse (97.7% Accuracy).

Features:
- 90+ Sprachen
- Layout-Erkennung (Tabellen, Spalten)
- Bounding Boxes pro Zeile/Wort
- Batch Processing

Benchmark-Basis: Researchify Invoice OCR Comparison 2025

Usage:
    POST /ocr - Bild OCR
    POST /ocr/layout - Mit Layout-Analyse
    POST /ocr/batch - Mehrere Bilder
    GET /health - Health Check
"""

import os
import gc
import tempfile
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import torch
from PIL import Image
import io

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("surya-ocr")

# Configuration
DEVICE = os.getenv("SURYA_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = int(os.getenv("SURYA_BATCH_SIZE", "4"))
DEFAULT_LANGS = os.getenv("SURYA_LANGS", "de,en").split(",")

# Initialize FastAPI
app = FastAPI(
    title="Surya OCR API",
    description="High-Accuracy OCR with Layout Analysis",
    version="1.0.0"
)

# Global models (lazy loading)
ocr_model = None
det_model = None
rec_model = None
layout_model = None


# =============================================================================
# DATA MODELS
# =============================================================================

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class TextLine(BaseModel):
    text: str
    confidence: float
    bbox: BoundingBox
    words: Optional[List[Dict[str, Any]]] = None


class LayoutBlock(BaseModel):
    type: str  # "text", "table", "figure", "header", "footer"
    bbox: BoundingBox
    lines: List[TextLine]


class OCRResult(BaseModel):
    text: str
    lines: List[TextLine]
    layout: Optional[List[LayoutBlock]] = None
    language: str
    confidence: float
    width: int
    height: int


class BatchOCRResult(BaseModel):
    results: List[OCRResult]
    total_images: int
    successful: int
    failed: int


# =============================================================================
# MODEL LOADING
# =============================================================================

def load_models():
    """Lädt Surya OCR Modelle."""
    global ocr_model, det_model, rec_model

    if ocr_model is None:
        from surya.ocr import run_ocr
        from surya.model.detection.model import load_model as load_det_model
        from surya.model.detection.model import load_processor as load_det_processor
        from surya.model.recognition.model import load_model as load_rec_model
        from surya.model.recognition.processor import load_processor as load_rec_processor

        logger.info(f"Loading Surya models on {DEVICE}...")

        # Detection Model
        det_model = load_det_model()
        det_processor = load_det_processor()

        # Recognition Model
        rec_model = load_rec_model()
        rec_processor = load_rec_processor()

        # Store for later use
        ocr_model = {
            "det_model": det_model,
            "det_processor": det_processor,
            "rec_model": rec_model,
            "rec_processor": rec_processor,
        }

        logger.info("Surya models loaded")

    return ocr_model


def load_layout_model():
    """Lädt Layout-Analyse Modell."""
    global layout_model

    if layout_model is None:
        from surya.model.detection.model import load_model as load_layout
        from surya.model.detection.model import load_processor as load_layout_processor

        logger.info("Loading layout model...")
        layout_model = {
            "model": load_layout(checkpoint="vikp/surya_layout3"),
            "processor": load_layout_processor(checkpoint="vikp/surya_layout3"),
        }
        logger.info("Layout model loaded")

    return layout_model


# =============================================================================
# OCR FUNCTIONS
# =============================================================================

def process_image(
    image: Image.Image,
    langs: List[str] = None,
    with_layout: bool = False,
) -> OCRResult:
    """
    Führt OCR auf einem Bild durch.

    Args:
        image: PIL Image
        langs: Sprachen (z.B. ["de", "en"])
        with_layout: Layout-Analyse durchführen

    Returns:
        OCRResult
    """
    from surya.ocr import run_ocr
    from surya.detection import batch_text_detection
    from surya.recognition import batch_recognition

    langs = langs or DEFAULT_LANGS
    models = load_models()

    # Text Detection
    det_results = batch_text_detection(
        [image],
        models["det_model"],
        models["det_processor"],
    )

    # Text Recognition
    rec_results = batch_recognition(
        [image],
        det_results,
        models["rec_model"],
        models["rec_processor"],
        languages=[langs],
    )

    # Parse results
    result = rec_results[0]
    lines = []
    full_text = []
    total_confidence = 0

    for line in result.text_lines:
        bbox = BoundingBox(
            x1=line.bbox[0],
            y1=line.bbox[1],
            x2=line.bbox[2],
            y2=line.bbox[3],
        )

        text_line = TextLine(
            text=line.text,
            confidence=line.confidence,
            bbox=bbox,
        )
        lines.append(text_line)
        full_text.append(line.text)
        total_confidence += line.confidence

    avg_confidence = total_confidence / len(lines) if lines else 0

    # Layout Analysis (optional)
    layout_blocks = None
    if with_layout:
        try:
            from surya.layout import batch_layout_detection

            layout_models = load_layout_model()
            layout_results = batch_layout_detection(
                [image],
                layout_models["model"],
                layout_models["processor"],
            )

            layout_blocks = []
            for block in layout_results[0].bboxes:
                layout_blocks.append(LayoutBlock(
                    type=block.label,
                    bbox=BoundingBox(
                        x1=block.bbox[0],
                        y1=block.bbox[1],
                        x2=block.bbox[2],
                        y2=block.bbox[3],
                    ),
                    lines=[],  # Könnte mit lines korreliert werden
                ))
        except Exception as e:
            logger.warning(f"Layout analysis failed: {e}")

    return OCRResult(
        text="\n".join(full_text),
        lines=lines,
        layout=layout_blocks,
        language=langs[0] if langs else "unknown",
        confidence=avg_confidence,
        width=image.width,
        height=image.height,
    )


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/health")
async def health():
    """Health Check."""
    return {
        "status": "healthy",
        "device": DEVICE,
        "default_langs": DEFAULT_LANGS,
        "models_loaded": ocr_model is not None,
    }


@app.post("/ocr", response_model=OCRResult)
async def ocr(
    file: UploadFile = File(...),
    langs: str = Query("de,en", description="Sprachen (komma-getrennt)"),
):
    """
    OCR auf einem Bild.

    Unterstützte Formate: PNG, JPG, JPEG, TIFF, BMP, WebP
    """
    try:
        # Bild laden
        content = await file.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")

        # OCR durchführen
        lang_list = [l.strip() for l in langs.split(",")]
        result = process_image(image, langs=lang_list, with_layout=False)

        return result

    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/layout", response_model=OCRResult)
async def ocr_with_layout(
    file: UploadFile = File(...),
    langs: str = Query("de,en", description="Sprachen"),
):
    """
    OCR mit Layout-Analyse.

    Erkennt zusätzlich:
    - Tabellen
    - Überschriften
    - Fußzeilen
    - Abbildungen
    """
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")

        lang_list = [l.strip() for l in langs.split(",")]
        result = process_image(image, langs=lang_list, with_layout=True)

        return result

    except Exception as e:
        logger.error(f"OCR layout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/path")
async def ocr_path(
    path: str = Form(...),
    langs: str = Form("de,en"),
    with_layout: bool = Form(False),
):
    """
    OCR auf einer lokalen Datei (für Docker-Volumes).
    """
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    try:
        image = Image.open(path).convert("RGB")
        lang_list = [l.strip() for l in langs.split(",")]
        result = process_image(image, langs=lang_list, with_layout=with_layout)
        return result

    except Exception as e:
        logger.error(f"OCR path error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/batch", response_model=BatchOCRResult)
async def ocr_batch(
    files: List[UploadFile] = File(...),
    langs: str = Query("de,en", description="Sprachen"),
):
    """
    Batch OCR auf mehreren Bildern.
    """
    results = []
    successful = 0
    failed = 0

    lang_list = [l.strip() for l in langs.split(",")]

    for file in files:
        try:
            content = await file.read()
            image = Image.open(io.BytesIO(content)).convert("RGB")
            result = process_image(image, langs=lang_list)
            results.append(result)
            successful += 1
        except Exception as e:
            logger.error(f"Batch OCR error for {file.filename}: {e}")
            failed += 1

    return BatchOCRResult(
        results=results,
        total_images=len(files),
        successful=successful,
        failed=failed,
    )


@app.get("/languages")
async def list_languages():
    """Listet unterstützte Sprachen."""
    # Surya unterstützt 90+ Sprachen via mBART
    common_langs = {
        "de": "German",
        "en": "English",
        "fr": "French",
        "es": "Spanish",
        "it": "Italian",
        "pt": "Portuguese",
        "nl": "Dutch",
        "pl": "Polish",
        "ru": "Russian",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
        "hi": "Hindi",
        "tr": "Turkish",
    }
    return {
        "total": "90+",
        "common": common_langs,
        "default": DEFAULT_LANGS,
    }


@app.on_event("shutdown")
async def shutdown():
    """Cleanup bei Shutdown."""
    global ocr_model, layout_model
    ocr_model = None
    layout_model = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Preload models
    load_models()

    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000)
