"""
WhisperX API Server
====================

Erweiterte Whisper-API mit:
- Word-Level Timestamps (wav2vec2 alignment)
- Speaker Diarization (pyannote.audio)
- Batch Processing (70x Realtime)

Benchmark-Basis: Modal.com WhisperX Comparison 2025

Usage:
    POST /transcribe - Audio transkribieren
    POST /transcribe/diarize - Mit Speaker-Erkennung
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

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisperx-api")

# Configuration
MODEL_SIZE = os.getenv("WHISPER_MODEL", "large-v3")
DEVICE = os.getenv("WHISPER_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16" if DEVICE == "cuda" else "int8")
BATCH_SIZE = int(os.getenv("WHISPER_BATCH_SIZE", "16"))
HF_TOKEN = os.getenv("HF_TOKEN", "")  # Für pyannote diarization

# Initialize FastAPI
app = FastAPI(
    title="WhisperX API",
    description="Word-Level Timestamps + Speaker Diarization",
    version="1.0.0"
)

# Global models (lazy loading)
whisper_model = None
align_model = None
align_metadata = None
diarize_pipeline = None


# =============================================================================
# MODELS
# =============================================================================

class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str
    words: Optional[List[Dict[str, Any]]] = None
    speaker: Optional[str] = None


class TranscriptionResult(BaseModel):
    text: str
    segments: List[TranscriptionSegment]
    language: str
    duration: float
    word_count: int
    has_word_timestamps: bool
    has_diarization: bool


# =============================================================================
# MODEL LOADING
# =============================================================================

def load_whisper_model():
    """Lädt WhisperX Modell."""
    global whisper_model
    if whisper_model is None:
        import whisperx
        logger.info(f"Loading WhisperX model: {MODEL_SIZE} on {DEVICE}")
        whisper_model = whisperx.load_model(
            MODEL_SIZE,
            DEVICE,
            compute_type=COMPUTE_TYPE,
        )
        logger.info("WhisperX model loaded")
    return whisper_model


def load_align_model(language: str):
    """Lädt Alignment-Modell für Word-Level Timestamps."""
    global align_model, align_metadata
    import whisperx

    # Cache pro Sprache
    if align_model is None or align_metadata.get("language") != language:
        logger.info(f"Loading alignment model for: {language}")
        align_model, align_metadata = whisperx.load_align_model(
            language_code=language,
            device=DEVICE
        )
        align_metadata["language"] = language
        logger.info("Alignment model loaded")

    return align_model, align_metadata


def load_diarize_pipeline():
    """Lädt Speaker Diarization Pipeline."""
    global diarize_pipeline
    if diarize_pipeline is None:
        if not HF_TOKEN:
            logger.warning("HF_TOKEN not set - diarization unavailable")
            return None

        from pyannote.audio import Pipeline
        logger.info("Loading diarization pipeline...")
        diarize_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=HF_TOKEN
        )
        if DEVICE == "cuda":
            diarize_pipeline.to(torch.device("cuda"))
        logger.info("Diarization pipeline loaded")

    return diarize_pipeline


# =============================================================================
# TRANSCRIPTION
# =============================================================================

def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
    align_words: bool = True,
    diarize: bool = False,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
) -> TranscriptionResult:
    """
    Transkribiert Audio mit WhisperX.

    Args:
        audio_path: Pfad zur Audiodatei
        language: Sprache (auto-detect wenn None)
        align_words: Word-Level Timestamps berechnen
        diarize: Speaker Diarization durchführen
        min_speakers: Minimum Anzahl Sprecher
        max_speakers: Maximum Anzahl Sprecher

    Returns:
        TranscriptionResult mit Segmenten und Metadaten
    """
    import whisperx

    # 1. Whisper Transcription
    model = load_whisper_model()

    logger.info(f"Transcribing: {audio_path}")
    audio = whisperx.load_audio(audio_path)

    result = model.transcribe(
        audio,
        batch_size=BATCH_SIZE,
        language=language,
    )

    detected_language = result.get("language", language or "en")
    logger.info(f"Detected language: {detected_language}")

    # 2. Word-Level Alignment
    has_word_timestamps = False
    if align_words:
        try:
            align_model_instance, metadata = load_align_model(detected_language)
            result = whisperx.align(
                result["segments"],
                align_model_instance,
                metadata,
                audio,
                DEVICE,
                return_char_alignments=False,
            )
            has_word_timestamps = True
            logger.info("Word alignment complete")
        except Exception as e:
            logger.warning(f"Alignment failed: {e}")

    # 3. Speaker Diarization
    has_diarization = False
    if diarize:
        pipeline = load_diarize_pipeline()
        if pipeline:
            try:
                diarize_segments = pipeline(
                    audio_path,
                    min_speakers=min_speakers,
                    max_speakers=max_speakers,
                )
                result = whisperx.assign_word_speakers(diarize_segments, result)
                has_diarization = True
                logger.info("Diarization complete")
            except Exception as e:
                logger.warning(f"Diarization failed: {e}")

    # 4. Ergebnis aufbereiten
    segments = []
    full_text = []
    total_words = 0

    for seg in result.get("segments", []):
        words = seg.get("words", [])
        total_words += len(words)

        segment = TranscriptionSegment(
            start=seg.get("start", 0),
            end=seg.get("end", 0),
            text=seg.get("text", "").strip(),
            words=[
                {
                    "word": w.get("word", ""),
                    "start": w.get("start"),
                    "end": w.get("end"),
                    "score": w.get("score"),
                }
                for w in words
            ] if words else None,
            speaker=seg.get("speaker"),
        )
        segments.append(segment)
        full_text.append(segment.text)

    # Dauer berechnen
    duration = segments[-1].end if segments else 0

    return TranscriptionResult(
        text=" ".join(full_text),
        segments=segments,
        language=detected_language,
        duration=duration,
        word_count=total_words,
        has_word_timestamps=has_word_timestamps,
        has_diarization=has_diarization,
    )


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/health")
async def health():
    """Health Check."""
    return {
        "status": "healthy",
        "model": MODEL_SIZE,
        "device": DEVICE,
        "compute_type": COMPUTE_TYPE,
        "diarization_available": bool(HF_TOKEN),
    }


@app.post("/transcribe", response_model=TranscriptionResult)
async def transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="Sprache (z.B. 'de', 'en')"),
    align_words: bool = Query(True, description="Word-Level Timestamps"),
):
    """
    Transkribiert eine Audiodatei.

    Unterstützte Formate: mp3, wav, m4a, flac, ogg, webm
    """
    # Datei speichern
    suffix = Path(file.filename).suffix or ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        audio_path = tmp.name

    try:
        result = transcribe_audio(
            audio_path=audio_path,
            language=language,
            align_words=align_words,
            diarize=False,
        )
        return result

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup
        try:
            os.unlink(audio_path)
        except:
            pass


@app.post("/transcribe/diarize", response_model=TranscriptionResult)
async def transcribe_with_diarization(
    file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="Sprache"),
    min_speakers: Optional[int] = Query(None, description="Min. Anzahl Sprecher"),
    max_speakers: Optional[int] = Query(None, description="Max. Anzahl Sprecher"),
):
    """
    Transkribiert mit Speaker Diarization.

    Erfordert HF_TOKEN für pyannote.audio.
    Identifiziert verschiedene Sprecher (SPEAKER_00, SPEAKER_01, etc.)
    """
    if not HF_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Diarization unavailable: HF_TOKEN not configured"
        )

    # Datei speichern
    suffix = Path(file.filename).suffix or ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        audio_path = tmp.name

    try:
        result = transcribe_audio(
            audio_path=audio_path,
            language=language,
            align_words=True,
            diarize=True,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )
        return result

    except Exception as e:
        logger.error(f"Diarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        try:
            os.unlink(audio_path)
        except:
            pass


@app.post("/transcribe/path")
async def transcribe_path(
    path: str = Form(...),
    language: Optional[str] = Form(None),
    align_words: bool = Form(True),
    diarize: bool = Form(False),
):
    """
    Transkribiert eine lokale Datei (für Docker-Volumes).
    """
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    try:
        result = transcribe_audio(
            audio_path=path,
            language=language,
            align_words=align_words,
            diarize=diarize,
        )
        return result

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """Listet verfügbare Modelle."""
    return {
        "available": [
            "tiny", "tiny.en",
            "base", "base.en",
            "small", "small.en",
            "medium", "medium.en",
            "large-v2", "large-v3"
        ],
        "current": MODEL_SIZE,
        "device": DEVICE,
    }


@app.on_event("shutdown")
async def shutdown():
    """Cleanup bei Shutdown."""
    global whisper_model, align_model, diarize_pipeline
    whisper_model = None
    align_model = None
    diarize_pipeline = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Preload model
    load_whisper_model()

    # Run server
    uvicorn.run(app, host="0.0.0.0", port=9000)
