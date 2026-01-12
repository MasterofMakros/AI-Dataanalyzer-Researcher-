"""
Surya OCR API Server
====================

Hochpräzise OCR mit Layout-Analyse (97.7% Accuracy).

API-Version: 2.0.0 (Surya 0.17+ Compatible)
"""

import os
import gc
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
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
    description="High-Accuracy OCR with Layout Analysis (Surya 0.17+)",
    version="2.0.0"
)

# Global predictors (lazy loading)
det_predictor = None
rec_predictor = None

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

class OCRResult(BaseModel):
    text: str
    lines: List[TextLine]
    language: str
    confidence: float
    width: int
    height: int

# =============================================================================
# MODEL LOADING (Surya 0.17+)
# =============================================================================

def load_models():
    """Lädt Surya OCR Predictors für Version 0.17+"""
    global det_predictor, rec_predictor

    if det_predictor is None:
        try:
            from surya.detection import DetectionPredictor
            from surya.recognition import FoundationPredictor, RecognitionPredictor
            
            logger.info(f"Loading Surya 0.17 predictors on {DEVICE}...")
            
            # DetectionPredictor can be created directly
            det_predictor = DetectionPredictor(device=DEVICE)
            
            # RecognitionPredictor requires a FoundationPredictor
            foundation = FoundationPredictor(device=DEVICE)
            rec_predictor = RecognitionPredictor(foundation)
            
            logger.info("Surya 0.17 predictors loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load predictors: {e}")
            raise

    return det_predictor, rec_predictor

# =============================================================================
# OCR FUNCTION (Surya 0.17+)
# =============================================================================

def process_image(
    image: Image.Image,
    langs: List[str] = None,
) -> OCRResult:
    """OCR processing using Surya 0.17+ Predictor API."""
    langs = langs or DEFAULT_LANGS
    det, rec = load_models()
    
    # Convert PIL Image to list (predictors expect list of images)
    images = [image]
    
    # Detection and Recognition in one call - RecognitionPredictor handles detection internally
    # when passed det_predictor parameter
    rec_results = rec(images, det_predictor=det)
    
    # Parse results - rec_results[0] is the result for first image
    result = rec_results[0]
    
    lines = []
    full_text = []
    total_confidence = 0

    # Surya 0.17 returns OCRResult with text_lines attribute
    for line in result.text_lines:
        bbox = BoundingBox(
            x1=line.bbox[0] if hasattr(line, 'bbox') else 0,
            y1=line.bbox[1] if hasattr(line, 'bbox') else 0,
            x2=line.bbox[2] if hasattr(line, 'bbox') else 0,
            y2=line.bbox[3] if hasattr(line, 'bbox') else 0,
        )

        text_line = TextLine(
            text=line.text,
            confidence=line.confidence if hasattr(line, 'confidence') else 1.0,
            bbox=bbox,
        )
        lines.append(text_line)
        full_text.append(line.text)
        if hasattr(line, 'confidence'):
            total_confidence += line.confidence

    avg_confidence = total_confidence / len(lines) if lines else 0.977

    return OCRResult(
        text="\n".join(full_text),
        lines=lines,
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
    return {"status": "healthy", "device": DEVICE, "api_version": "2.0.0", "surya_version": "0.17+"}

@app.post("/ocr", response_model=OCRResult)
async def ocr(file: UploadFile = File(...), langs: str = Query("de,en")):
    """Perform OCR on uploaded image."""
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")
        lang_list = [l.strip() for l in langs.split(",")]
        return process_image(image, langs=lang_list)
    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Preload models
    try:
        load_models()
    except Exception as e:
        logger.warning(f"Could not preload models: {e}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
