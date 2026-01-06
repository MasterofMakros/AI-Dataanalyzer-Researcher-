"""
Whisper API Server
Exposes faster-whisper as a REST API for n8n integration.
"""
import os
import tempfile
import logging
from flask import Flask, request, jsonify
from faster_whisper import WhisperModel

# Configuration
MODEL_SIZE = os.getenv("WHISPER_MODEL", "large-v3")
DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisper-api")

# Initialize Flask
app = Flask(__name__)

# Load model (lazy)
model = None

def get_model():
    global model
    if model is None:
        logger.info(f"Loading Whisper model: {MODEL_SIZE} on {DEVICE}")
        model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE
        )
        logger.info("Model loaded successfully")
    return model


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "model": MODEL_SIZE, "device": DEVICE})


@app.route("/transcribe", methods=["POST"])
def transcribe():
    """
    Transcribe audio file.
    
    Accepts:
    - multipart/form-data with 'file' field
    - JSON with 'path' field (local file path)
    
    Returns:
    - JSON with 'text', 'segments', 'language', 'duration'
    """
    try:
        whisper = get_model()
        
        # Handle file upload or path
        if "file" in request.files:
            file = request.files["file"]
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                file.save(tmp.name)
                audio_path = tmp.name
        elif request.is_json and "path" in request.json:
            audio_path = request.json["path"]
        else:
            return jsonify({"error": "No file or path provided"}), 400
        
        # Get optional parameters
        language = request.args.get("language", None)
        task = request.args.get("task", "transcribe")  # or "translate"
        
        logger.info(f"Transcribing: {audio_path}")
        
        # Transcribe
        segments, info = whisper.transcribe(
            audio_path,
            language=language,
            task=task,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=800)
        )
        
        # Collect results
        text_segments = []
        full_text = []
        
        for segment in segments:
            text_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            full_text.append(segment.text.strip())
        
        result = {
            "text": " ".join(full_text),
            "segments": text_segments,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration
        }
        
        logger.info(f"Transcription complete: {len(text_segments)} segments, {info.duration:.1f}s")
        
        # Cleanup temp file if uploaded
        if "file" in request.files:
            os.unlink(audio_path)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/models", methods=["GET"])
def list_models():
    """List available model sizes."""
    return jsonify({
        "available": ["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        "current": MODEL_SIZE
    })


if __name__ == "__main__":
    # Preload model
    get_model()
    
    # Run server
    app.run(host="0.0.0.0", port=9000, debug=False)
