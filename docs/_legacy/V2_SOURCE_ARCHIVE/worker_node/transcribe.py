"""
Transcription Service - Uses faster-whisper for GPU-accelerated transcription.
Part of TRACK-004: Smart Media Transcription
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("worker.transcribe")

# Check if faster-whisper is available
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Transcription disabled.")


class TranscriptionService:
    """
    GPU-accelerated transcription using faster-whisper.
    Falls back to CPU if CUDA not available.
    """
    
    def __init__(self, model_size: str = "large-v3", device: str = "auto"):
        self.model: Optional[WhisperModel] = None
        self.model_size = model_size
        
        if not WHISPER_AVAILABLE:
            logger.error("Transcription service unavailable - faster-whisper not installed")
            return
            
        # Detect best device
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        
        compute_type = "float16" if device == "cuda" else "int8"
        
        logger.info(f"Loading Whisper model '{model_size}' on {device} ({compute_type})...")
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
    
    def transcribe(self, audio_path: str, language: str = "de") -> Tuple[str, dict]:
        """
        Transcribe an audio/video file.
        
        Args:
            audio_path: Path to media file
            language: Language code (de, en, etc.)
            
        Returns:
            Tuple of (transcript_text, metadata_dict)
        """
        if not self.model:
            return "", {"error": "Model not loaded"}
        
        if not os.path.exists(audio_path):
            return "", {"error": f"File not found: {audio_path}"}
        
        logger.info(f"Transcribing: {audio_path}")
        
        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                vad_filter=True,  # Voice Activity Detection
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            
            # Collect all segments
            transcript_lines = []
            for segment in segments:
                timestamp = f"[{self._format_time(segment.start)} -> {self._format_time(segment.end)}]"
                transcript_lines.append(f"{timestamp} {segment.text.strip()}")
            
            transcript = "\n".join(transcript_lines)
            
            metadata = {
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments_count": len(transcript_lines),
            }
            
            logger.info(f"Transcription complete: {len(transcript_lines)} segments, {info.duration:.1f}s duration")
            return transcript, metadata
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return "", {"error": str(e)}
    
    def transcribe_to_sidecar(self, media_path: str, language: str = "de") -> Optional[str]:
        """
        Transcribe and save as .transcript.md sidecar file.
        
        Returns path to sidecar file or None on failure.
        """
        transcript, metadata = self.transcribe(media_path, language)
        
        if not transcript:
            return None
        
        # Create sidecar path
        media_path = Path(media_path)
        sidecar_path = media_path.with_suffix(media_path.suffix + ".transcript.md")
        
        # Build markdown content
        content = f"""# Transcript: {media_path.name}

## Metadata
- **Duration**: {metadata.get('duration', 0):.1f} seconds
- **Language**: {metadata.get('language', 'unknown')} ({metadata.get('language_probability', 0):.0%} confidence)
- **Segments**: {metadata.get('segments_count', 0)}

## Full Transcript

{transcript}
"""
        
        try:
            sidecar_path.write_text(content, encoding="utf-8")
            logger.info(f"Sidecar created: {sidecar_path}")
            return str(sidecar_path)
        except Exception as e:
            logger.error(f"Failed to write sidecar: {e}")
            return None
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds as MM:SS"""
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"


# Singleton instance
_service: Optional[TranscriptionService] = None

def get_transcription_service() -> TranscriptionService:
    """Get or create the transcription service singleton."""
    global _service
    if _service is None:
        _service = TranscriptionService()
    return _service


if __name__ == "__main__":
    # Test run
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        service = get_transcription_service()
        result = service.transcribe_to_sidecar(sys.argv[1])
        print(f"Result: {result}")
    else:
        print("Usage: python transcribe.py <audio_file>")
