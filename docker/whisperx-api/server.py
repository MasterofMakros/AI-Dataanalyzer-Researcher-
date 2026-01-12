"""
WhisperX API Server
====================

FastAPI wrapper for WhisperX with:
- Word-Level Timestamps (wav2vec2 alignment)
- Speaker Diarization (pyannote.audio)
- Batch Processing (70x Realtime)

Based on: https://github.com/m-bain/whisperX (v3.7.4+)
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

# =============================================================================
# PyTorch 2.6+/2.8 Compatibility Fix (from WhisperX PR #1313)
# =============================================================================
# Must be applied BEFORE any model loading occurs
try:
    from omegaconf import DictConfig, ListConfig
    from omegaconf.base import ContainerMetadata, Metadata
    from omegaconf.nodes import AnyNode, BooleanNode, FloatNode, IntegerNode, StringNode
    from pyannote.audio.core.model import Introspection
    from pyannote.audio.core.task import Problem, Resolution, Specifications
    from torch.torch_version import TorchVersion
    from collections import OrderedDict, defaultdict
    import typing
    
    torch.serialization.add_safe_globals([
        # OmegaConf types
        DictConfig, ListConfig, ContainerMetadata, Metadata,
        AnyNode, BooleanNode, FloatNode, IntegerNode, StringNode,
        # Python builtins
        typing.Any, list, dict, tuple, set, frozenset,
        int, float, bool, str, bytes, OrderedDict, defaultdict,
        # Pyannote + Torch types
        TorchVersion, Introspection, Specifications, Problem, Resolution,
    ])
    print("✓ Added safe globals for PyTorch 2.8+ compatibility")
except Exception as e:
    print(f"⚠ Could not add all safe globals: {e}")
    # Fallback: monkey patch to disable weights_only
    _original_load = torch.load
    def _patched_load(*args, **kwargs):
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return _original_load(*args, **kwargs)
    torch.load = _patched_load
    print("✓ Applied torch.load fallback patch")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisperx-api")

# Configuration
MODEL_SIZE = os.getenv("WHISPER_MODEL", "large-v3")
DEVICE = os.getenv("WHISPER_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16" if DEVICE == "cuda" else "int8")
BATCH_SIZE = int(os.getenv("WHISPER_BATCH_SIZE", "16"))
HF_TOKEN = os.getenv("HF_TOKEN", "")  # Required for pyannote diarization

# Initialize FastAPI
app = FastAPI(
    title="WhisperX API",
    description="Word-level transcription with speaker diarization",
    version="2.1.4"
)

# Global model cache
whisper_model = None
align_model = None
align_metadata = None
diarize_model = None


# =============================================================================
# MODELS
# =============================================================================

class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    words: Optional[List[Dict[str, Any]]] = None


class TranscriptionResult(BaseModel):
    text: str
    segments: List[TranscriptionSegment]
    language: str
    duration: Optional[float] = None


# =============================================================================
# MODEL LOADING
# =============================================================================

def load_whisper_model():
    """Load WhisperX model."""
    global whisper_model
    if whisper_model is None:
        import whisperx
        logger.info(f"Loading WhisperX model: {MODEL_SIZE} on {DEVICE}")
        whisper_model = whisperx.load_model(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE
        )
        logger.info("WhisperX model loaded successfully")
    return whisper_model


def load_align_model(language_code: str):
    """Load alignment model for word-level timestamps."""
    global align_model, align_metadata
    import whisperx
    if align_model is None or align_metadata.get("language") != language_code:
        logger.info(f"Loading alignment model for: {language_code}")
        align_model, align_metadata = whisperx.load_align_model(
            language_code=language_code,
            device=DEVICE
        )
        align_metadata["language"] = language_code
    return align_model, align_metadata


def load_diarize_model():
    """Load diarization pipeline."""
    global diarize_model
    if diarize_model is None and HF_TOKEN:
        import whisperx
        logger.info("Loading diarization pipeline...")
        diarize_model = whisperx.DiarizationPipeline(
            use_auth_token=HF_TOKEN,
            device=DEVICE
        )
        logger.info("Diarization pipeline loaded")
    return diarize_model


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": MODEL_SIZE,
        "device": DEVICE,
        "compute_type": COMPUTE_TYPE,
        "cuda_available": torch.cuda.is_available(),
        "diarization_available": bool(HF_TOKEN)
    }


@app.post("/transcribe", response_model=TranscriptionResult)
async def transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="Language code (auto-detect if not set)"),
    align: bool = Query(True, description="Enable word-level alignment"),
    diarize: bool = Query(False, description="Enable speaker diarization")
):
    """
    Transcribe audio file with optional word-level alignment and diarization.
    """
    import whisperx
    
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Load audio
        audio = whisperx.load_audio(tmp_path)
        
        # Transcribe
        model = load_whisper_model()
        result = model.transcribe(audio, batch_size=BATCH_SIZE, language=language)
        
        detected_language = result.get("language", language or "en")
        
        # Align (word-level timestamps)
        if align:
            try:
                align_model_instance, metadata = load_align_model(detected_language)
                result = whisperx.align(
                    result["segments"],
                    align_model_instance,
                    metadata,
                    audio,
                    DEVICE,
                    return_char_alignments=False
                )
            except Exception as e:
                logger.warning(f"Alignment failed: {e}")
        
        # Diarize (speaker identification)
        if diarize and HF_TOKEN:
            try:
                diarize_pipe = load_diarize_model()
                if diarize_pipe:
                    diarize_segments = diarize_pipe(audio)
                    result = whisperx.assign_word_speakers(diarize_segments, result)
            except Exception as e:
                logger.warning(f"Diarization failed: {e}")
        
        # Format response
        segments = []
        full_text = []
        
        for seg in result.get("segments", []):
            segment = TranscriptionSegment(
                start=seg.get("start", 0),
                end=seg.get("end", 0),
                text=seg.get("text", "").strip(),
                speaker=seg.get("speaker"),
                words=seg.get("words")
            )
            segments.append(segment)
            full_text.append(segment.text)
        
        return TranscriptionResult(
            text=" ".join(full_text),
            segments=segments,
            language=detected_language,
            duration=len(audio) / 16000 if audio is not None else None
        )
    
    finally:
        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)
        gc.collect()
        if DEVICE == "cuda":
            torch.cuda.empty_cache()


@app.post("/v1/audio/transcriptions")
async def openai_compatible_transcribe(
    file: UploadFile = File(...),
    language: str = Form(None),
    response_format: str = Form("json")
):
    """
    OpenAI-compatible transcription endpoint.
    """
    result = await transcribe(file=file, language=language, align=True, diarize=False)
    
    if response_format == "verbose_json":
        return {
            "text": result.text,
            "language": result.language,
            "duration": result.duration,
            "segments": [seg.dict() for seg in result.segments]
        }
    else:
        return {"text": result.text}


# =============================================================================
# STARTUP
# =============================================================================

@app.on_event("startup")
async def startup():
    """Pre-load models on startup."""
    logger.info(f"WhisperX API starting on {DEVICE}...")
    try:
        load_whisper_model()
        logger.info("Model pre-loaded successfully")
    except Exception as e:
        logger.error(f"Failed to pre-load model: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
