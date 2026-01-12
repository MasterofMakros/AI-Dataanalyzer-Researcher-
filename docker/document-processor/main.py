"""
Neural Vault Document Processor
================================

Unified GPU Service combining:
- Docling (97.9% Table Accuracy)
- Surya OCR (97.7% Accuracy)
- GLiNER (Zero-shot NER)

Endpoints:
    POST /process/document  - Unified processing with auto-routing
    POST /process/pdf       - PDF extraction via Docling
    POST /process/ocr       - OCR via Surya
    POST /process/pii       - PII detection via GLiNER
    POST /vector/embed      - Generate embeddings
    POST /vector/store      - Store in LanceDB
    POST /vector/search     - Semantic search
    GET  /health            - Health check
"""

import os
import gc
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import torch

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("document-processor")

# Configuration
DEVICE = os.getenv("PROCESSOR_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
GLINER_MODEL = os.getenv("GLINER_MODEL", "urchade/gliner_small-v2.1")
EMBED_MODEL = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-large")
SURYA_LANGS = os.getenv("SURYA_LANGS", "de,en").split(",")
LANCEDB_PATH = os.getenv("LANCEDB_PATH", "/data/lancedb")

# Initialize FastAPI
app = FastAPI(
    title="Neural Vault Document Processor",
    description="Unified GPU Service: Docling + Surya OCR + GLiNER",
    version="2.0.0"
)


# =============================================================================
# MODELS (Lazy Loading)
# =============================================================================

class Models:
    """Global model container with lazy loading."""
    docling_converter = None
    gliner_model = None
    embed_model = None
    surya_models = None
    lancedb_connection = None


def get_docling():
    """Lazy load Docling converter."""
    if Models.docling_converter is None:
        logger.info("Loading Docling converter...")
        from docling.document_converter import DocumentConverter
        Models.docling_converter = DocumentConverter()
        logger.info("Docling loaded")
    return Models.docling_converter


def get_gliner():
    """Lazy load GLiNER model."""
    if Models.gliner_model is None:
        logger.info(f"Loading GLiNER model: {GLINER_MODEL}...")
        from gliner import GLiNER
        try:
            Models.gliner_model = GLiNER.from_pretrained(GLINER_MODEL)
        except Exception:
            logger.warning("Failed to load specified model, using base")
            Models.gliner_model = GLiNER.from_pretrained("urchade/gliner_base")
        logger.info("GLiNER loaded")
    return Models.gliner_model


def get_embed_model():
    """Lazy load embedding model."""
    if Models.embed_model is None:
        logger.info(f"Loading embedding model: {EMBED_MODEL}...")
        from sentence_transformers import SentenceTransformer
        Models.embed_model = SentenceTransformer(EMBED_MODEL)
        logger.info("Embedding model loaded")
    return Models.embed_model


def get_surya():
    """Lazy load Surya OCR models."""
    if Models.surya_models is None:
        logger.info("Loading Surya OCR models...")
        from surya.model.detection.model import load_model as load_det_model
        from surya.model.detection.model import load_processor as load_det_processor
        from surya.model.recognition.model import load_model as load_rec_model
        from surya.model.recognition.processor import load_processor as load_rec_processor

        Models.surya_models = {
            "det_model": load_det_model(),
            "det_processor": load_det_processor(),
            "rec_model": load_rec_model(),
            "rec_processor": load_rec_processor(),
        }
        logger.info("Surya models loaded")
    return Models.surya_models


def get_lancedb():
    """Lazy load LanceDB connection."""
    if Models.lancedb_connection is None:
        logger.info(f"Connecting to LanceDB: {LANCEDB_PATH}...")
        import lancedb
        Path(LANCEDB_PATH).mkdir(parents=True, exist_ok=True)
        Models.lancedb_connection = lancedb.connect(LANCEDB_PATH)
        logger.info("LanceDB connected")
    return Models.lancedb_connection


# =============================================================================
# DATA MODELS
# =============================================================================

class ProcessorType(str, Enum):
    DOCLING = "docling"
    SURYA = "surya"
    AUTO = "auto"


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class TextLine(BaseModel):
    text: str
    confidence: float
    bbox: Optional[BoundingBox] = None


class DocumentResult(BaseModel):
    text: str
    markdown: Optional[str] = None
    lines: Optional[List[TextLine]] = None
    processor: str
    confidence: float = 0.0
    pages: int = 0
    tables_count: int = 0
    metadata: Dict[str, Any] = {}


class PiiRequest(BaseModel):
    text: str
    labels: List[str] = ["person", "iban", "date", "phone_number", "email"]


class PiiEntity(BaseModel):
    text: str
    label: str
    score: float
    start: int
    end: int


class PiiResult(BaseModel):
    entities: List[PiiEntity]
    masked_text: Optional[str] = None


class VectorStoreRequest(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = {}


class VectorSearchRequest(BaseModel):
    query: str
    limit: int = 5
    min_score: float = 0.0


# =============================================================================
# ROUTING LOGIC
# =============================================================================

# Extension → Processor mapping
PROCESSOR_ROUTING = {
    # Docling (structured documents)
    ".pdf": ProcessorType.DOCLING,
    ".docx": ProcessorType.DOCLING,
    ".pptx": ProcessorType.DOCLING,
    ".xlsx": ProcessorType.DOCLING,

    # Surya OCR (images)
    ".jpg": ProcessorType.SURYA,
    ".jpeg": ProcessorType.SURYA,
    ".png": ProcessorType.SURYA,
    ".tiff": ProcessorType.SURYA,
    ".tif": ProcessorType.SURYA,
    ".bmp": ProcessorType.SURYA,
    ".webp": ProcessorType.SURYA,
}


def get_processor(filename: str) -> ProcessorType:
    """Determine processor based on file extension."""
    ext = Path(filename).suffix.lower()
    return PROCESSOR_ROUTING.get(ext, ProcessorType.DOCLING)


# =============================================================================
# PROCESSING FUNCTIONS
# =============================================================================

def process_with_docling(filepath: str) -> DocumentResult:
    """Process document with Docling."""
    converter = get_docling()
    result = converter.convert(filepath)

    # Export to markdown
    markdown = result.document.export_to_markdown()

    # Count tables (simplified)
    tables_count = markdown.count("|---") // 2  # Rough estimate

    return DocumentResult(
        text=markdown,
        markdown=markdown,
        processor="docling",
        confidence=0.979,  # Benchmark value
        pages=len(result.document.pages) if hasattr(result.document, 'pages') else 0,
        tables_count=tables_count,
        metadata={
            "format": Path(filepath).suffix,
        }
    )


def process_with_surya(filepath: str, langs: List[str] = None) -> DocumentResult:
    """Process image with Surya OCR."""
    from PIL import Image
    from surya.detection import batch_text_detection
    from surya.recognition import batch_recognition

    langs = langs or SURYA_LANGS
    models = get_surya()

    # Load image
    image = Image.open(filepath).convert("RGB")

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
        text_line = TextLine(
            text=line.text,
            confidence=line.confidence,
            bbox=BoundingBox(
                x1=line.bbox[0],
                y1=line.bbox[1],
                x2=line.bbox[2],
                y2=line.bbox[3],
            ) if hasattr(line, 'bbox') else None,
        )
        lines.append(text_line)
        full_text.append(line.text)
        total_confidence += line.confidence

    avg_confidence = total_confidence / len(lines) if lines else 0

    return DocumentResult(
        text="\n".join(full_text),
        lines=lines,
        processor="surya",
        confidence=avg_confidence,
        pages=1,
        metadata={
            "width": image.width,
            "height": image.height,
            "languages": langs,
        }
    )


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/health")
def health():
    """Health check endpoint."""
    gpu_info = None
    if torch.cuda.is_available():
        try:
            gpu_info = {
                "name": torch.cuda.get_device_name(0),
                "memory_total_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2),
                "memory_allocated_gb": round(torch.cuda.memory_allocated(0) / 1e9, 2),
            }
        except Exception:
            pass

    return {
        "status": "healthy",
        "device": DEVICE,
        "mode": "GPU" if DEVICE == "cuda" and torch.cuda.is_available() else "CPU",
        "gpu_available": torch.cuda.is_available(),
        "gpu_info": gpu_info,
        "config": {
            "gliner_model": GLINER_MODEL,
            "embed_model": EMBED_MODEL,
            "surya_langs": SURYA_LANGS,
        },
        "models_loaded": {
            "docling": Models.docling_converter is not None,
            "surya": Models.surya_models is not None,
            "gliner": Models.gliner_model is not None,
            "embedding": Models.embed_model is not None,
            "lancedb": Models.lancedb_connection is not None,
        }
    }


@app.post("/process/document", response_model=DocumentResult)
async def process_document(
    file: UploadFile = File(...),
    processor: ProcessorType = Query(ProcessorType.AUTO, description="Processor to use"),
    langs: str = Query("de,en", description="Languages for OCR"),
):
    """
    Unified document processing endpoint.

    Auto-routes to optimal processor:
    - PDF/DOCX/PPTX/XLSX → Docling (97.9% table accuracy)
    - Images → Surya OCR (97.7% accuracy)
    """
    try:
        # Save upload to temp file
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Auto-routing
        if processor == ProcessorType.AUTO:
            processor = get_processor(file.filename)
            logger.info(f"Auto-routed {file.filename} → {processor.value}")

        # Process
        if processor == ProcessorType.SURYA:
            lang_list = [l.strip() for l in langs.split(",")]
            result = process_with_surya(tmp_path, lang_list)
        else:
            result = process_with_docling(tmp_path)

        # Cleanup
        os.remove(tmp_path)

        return result

    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/pdf", response_model=DocumentResult)
async def process_pdf(file: UploadFile = File(...)):
    """Process PDF with Docling (97.9% table accuracy)."""
    return await process_document(file, processor=ProcessorType.DOCLING)


@app.post("/process/ocr", response_model=DocumentResult)
async def process_ocr(
    file: UploadFile = File(...),
    langs: str = Query("de,en", description="Languages"),
):
    """OCR with Surya (97.7% accuracy)."""
    return await process_document(file, processor=ProcessorType.SURYA, langs=langs)


@app.post("/process/pii", response_model=PiiResult)
def detect_pii(request: PiiRequest):
    """
    Detect PII entities in text using GLiNER.

    Labels: person, iban, date, phone_number, email, address, organization
    """
    model = get_gliner()

    # Predict entities
    entities = model.predict_entities(request.text, request.labels)

    # Convert to response format
    pii_entities = []
    for e in entities:
        pii_entities.append(PiiEntity(
            text=e["text"],
            label=e["label"],
            score=float(e["score"]),
            start=e.get("start", 0),
            end=e.get("end", 0),
        ))

    # Optional: Generate masked text
    masked_text = request.text
    for entity in sorted(pii_entities, key=lambda x: x.start, reverse=True):
        if entity.score > 0.6:
            mask = f"[{entity.label.upper()}]"
            masked_text = masked_text[:entity.start] + mask + masked_text[entity.end:]

    return PiiResult(entities=pii_entities, masked_text=masked_text)


@app.post("/vector/embed")
def create_embedding(payload: VectorStoreRequest):
    """Generate embedding for text."""
    model = get_embed_model()
    vector = model.encode(payload.text).tolist()
    return {"vector": vector, "dim": len(vector)}


@app.post("/vector/store")
def store_vector(payload: VectorStoreRequest):
    """Store document in LanceDB."""
    import pyarrow as pa

    model = get_embed_model()
    db = get_lancedb()

    # Generate embedding
    vector = model.encode(payload.text).tolist()

    # Table name
    table_name = "conductor_docs"

    # Prepare data
    data = [{
        "vector": vector,
        "id": payload.id,
        "text": payload.text[:10000],  # Limit text size
        "metadata": json.dumps(payload.metadata),
    }]

    try:
        table = db.open_table(table_name)
        table.add(data)
    except Exception:
        # Create table if not exists
        table = db.create_table(table_name, data=data)

    return {"status": "stored", "id": payload.id}


@app.post("/vector/search")
def search_vectors(payload: VectorSearchRequest):
    """Semantic search in LanceDB."""
    model = get_embed_model()
    db = get_lancedb()

    query_vec = model.encode(payload.query).tolist()

    try:
        table = db.open_table("conductor_docs")
        results = table.search(query_vec).limit(payload.limit).to_list()

        # Parse metadata
        for r in results:
            if "metadata" in r and isinstance(r["metadata"], str):
                try:
                    r["metadata"] = json.loads(r["metadata"])
                except:
                    pass

        return {"results": results}
    except Exception as e:
        logger.warning(f"Search failed: {e}")
        return {"results": []}


@app.get("/processors")
def list_processors():
    """List available processors and their capabilities."""
    return {
        "docling": {
            "extensions": [".pdf", ".docx", ".pptx", ".xlsx"],
            "benchmark": "97.9% table accuracy",
            "gpu": True,
        },
        "surya": {
            "extensions": [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"],
            "benchmark": "97.7% OCR accuracy",
            "languages": "90+",
            "gpu": True,
        },
        "gliner": {
            "task": "NER/PII detection",
            "labels": ["person", "iban", "date", "phone_number", "email", "address", "organization"],
            "gpu": True,
        },
    }


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    Models.docling_converter = None
    Models.gliner_model = None
    Models.embed_model = None
    Models.surya_models = None
    Models.lancedb_connection = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Startup banner
    mode = "GPU" if DEVICE == "cuda" and torch.cuda.is_available() else "CPU"
    logger.info("=" * 60)
    logger.info("Neural Vault Document Processor v2.0.0")
    logger.info("=" * 60)
    logger.info(f"Mode: {mode}")
    logger.info(f"Device: {DEVICE}")
    logger.info(f"GPU Available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        try:
            logger.info(f"GPU Name: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        except Exception:
            pass
    else:
        logger.info("Running in CPU-only mode (slower but functional)")
        logger.info(f"Tip: Use smaller models for better CPU performance")

    logger.info("-" * 60)
    logger.info(f"GLiNER Model: {GLINER_MODEL}")
    logger.info(f"Embed Model: {EMBED_MODEL}")
    logger.info(f"Surya Langs: {SURYA_LANGS}")
    logger.info(f"LanceDB Path: {LANCEDB_PATH}")
    logger.info("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
