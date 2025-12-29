"""
Neural Vault WhisperX Client
============================

Client für den WhisperX API Service mit:
- Word-Level Timestamps
- Speaker Diarization
- Fallback auf faster-whisper

Usage:
    from scripts.services.whisperx_client import WhisperXClient

    client = WhisperXClient()
    result = client.transcribe("/path/to/audio.mp3")

    # Mit Diarization
    result = client.transcribe_with_speakers("/path/to/audio.mp3")
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

# Projekt-Root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.feature_flags import is_enabled


# =============================================================================
# KONFIGURATION
# =============================================================================

# WhisperX API URL
WHISPERX_URL = os.getenv("WHISPERX_URL", "http://localhost:9000")

# Fallback: Original faster-whisper API
WHISPER_URL = os.getenv("WHISPER_URL", "http://localhost:9000")

# Unterstützte Audio-Formate
AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".wma",
    ".aac", ".opus", ".webm"
}

# Video-Formate (Audio-Track extrahieren)
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".flv"
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Word:
    """Ein einzelnes Wort mit Timestamp."""
    word: str
    start: Optional[float] = None
    end: Optional[float] = None
    score: Optional[float] = None
    speaker: Optional[str] = None


@dataclass
class Segment:
    """Ein Transkriptions-Segment."""
    start: float
    end: float
    text: str
    words: List[Word] = field(default_factory=list)
    speaker: Optional[str] = None


@dataclass
class TranscriptionResult:
    """Vollständiges Transkriptions-Ergebnis."""
    text: str
    segments: List[Segment]
    language: str
    duration: float
    word_count: int
    has_word_timestamps: bool
    has_diarization: bool
    source: str  # "whisperx" oder "faster-whisper"

    def to_searchable_text(self) -> str:
        """Generiert durchsuchbaren Text mit Timestamps."""
        lines = []
        for seg in self.segments:
            timestamp = f"[{self._format_time(seg.start)}-{self._format_time(seg.end)}]"
            speaker = f" ({seg.speaker})" if seg.speaker else ""
            lines.append(f"{timestamp}{speaker} {seg.text}")
        return "\n".join(lines)

    def to_vtt(self) -> str:
        """Generiert WebVTT Untertitel."""
        lines = ["WEBVTT", ""]
        for i, seg in enumerate(self.segments, 1):
            start = self._format_vtt_time(seg.start)
            end = self._format_vtt_time(seg.end)
            lines.append(str(i))
            lines.append(f"{start} --> {end}")
            lines.append(seg.text)
            lines.append("")
        return "\n".join(lines)

    def get_speaker_segments(self) -> Dict[str, List[Segment]]:
        """Gruppiert Segmente nach Sprecher."""
        speakers = {}
        for seg in self.segments:
            speaker = seg.speaker or "UNKNOWN"
            if speaker not in speakers:
                speakers[speaker] = []
            speakers[speaker].append(seg)
        return speakers

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Formatiert Sekunden als MM:SS."""
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def _format_vtt_time(seconds: float) -> str:
        """Formatiert Sekunden als HH:MM:SS.mmm für VTT."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}"


# =============================================================================
# CLIENT
# =============================================================================

class WhisperXClient:
    """
    Client für WhisperX API Service.

    Unterstützt automatischen Fallback auf faster-whisper.
    """

    def __init__(
        self,
        whisperx_url: str = None,
        whisper_url: str = None,
        timeout: int = 600,
    ):
        """
        Initialisiert den Client.

        Args:
            whisperx_url: URL des WhisperX Service
            whisper_url: URL des Fallback faster-whisper Service
            timeout: Request Timeout in Sekunden
        """
        self.whisperx_url = whisperx_url or WHISPERX_URL
        self.whisper_url = whisper_url or WHISPER_URL
        self.timeout = timeout
        self._use_whisperx = None  # Lazy detection

    @property
    def use_whisperx(self) -> bool:
        """Prüft ob WhisperX verfügbar ist."""
        # Feature Flag prüfen
        if not is_enabled("USE_WHISPERX"):
            return False

        # Lazy detection
        if self._use_whisperx is None:
            self._use_whisperx = self._check_whisperx_available()
        return self._use_whisperx

    def _check_whisperx_available(self) -> bool:
        """Prüft ob WhisperX Service erreichbar ist."""
        try:
            response = requests.get(
                f"{self.whisperx_url}/health",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                # WhisperX hat diese Felder
                return data.get("has_word_timestamps", False) or \
                       "diarization_available" in data
        except:
            pass
        return False

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        align_words: bool = True,
    ) -> TranscriptionResult:
        """
        Transkribiert eine Audiodatei.

        Args:
            audio_path: Pfad zur Audio/Video-Datei
            language: Sprache (None = Auto-Detect)
            align_words: Word-Level Timestamps berechnen

        Returns:
            TranscriptionResult
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # WhisperX oder Fallback
        if self.use_whisperx:
            return self._transcribe_whisperx(
                audio_path, language, align_words, diarize=False
            )
        else:
            return self._transcribe_faster_whisper(audio_path, language)

    def transcribe_with_speakers(
        self,
        audio_path: str,
        language: Optional[str] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
    ) -> TranscriptionResult:
        """
        Transkribiert mit Speaker Diarization.

        Args:
            audio_path: Pfad zur Audio/Video-Datei
            language: Sprache (None = Auto-Detect)
            min_speakers: Minimum Anzahl Sprecher
            max_speakers: Maximum Anzahl Sprecher

        Returns:
            TranscriptionResult mit Speaker-IDs
        """
        if not self.use_whisperx:
            # Fallback ohne Diarization
            return self._transcribe_faster_whisper(audio_path, language)

        return self._transcribe_whisperx(
            audio_path, language, align_words=True, diarize=True,
            min_speakers=min_speakers, max_speakers=max_speakers
        )

    def _transcribe_whisperx(
        self,
        audio_path: str,
        language: Optional[str],
        align_words: bool,
        diarize: bool,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
    ) -> TranscriptionResult:
        """Transkription via WhisperX API."""
        endpoint = "/transcribe/diarize" if diarize else "/transcribe"
        url = f"{self.whisperx_url}{endpoint}"

        # Request vorbereiten
        with open(audio_path, "rb") as f:
            files = {"file": (Path(audio_path).name, f)}
            params = {}

            if language:
                params["language"] = language
            params["align_words"] = str(align_words).lower()

            if diarize:
                if min_speakers:
                    params["min_speakers"] = min_speakers
                if max_speakers:
                    params["max_speakers"] = max_speakers

            response = requests.post(
                url,
                files=files,
                params=params,
                timeout=self.timeout
            )

        if response.status_code != 200:
            raise RuntimeError(f"WhisperX error: {response.text}")

        data = response.json()
        return self._parse_whisperx_result(data)

    def _transcribe_faster_whisper(
        self,
        audio_path: str,
        language: Optional[str],
    ) -> TranscriptionResult:
        """Fallback: Transkription via faster-whisper API."""
        url = f"{self.whisper_url}/transcribe"

        with open(audio_path, "rb") as f:
            files = {"file": (Path(audio_path).name, f)}
            params = {}
            if language:
                params["language"] = language

            response = requests.post(
                url,
                files=files,
                params=params,
                timeout=self.timeout
            )

        if response.status_code != 200:
            raise RuntimeError(f"Whisper error: {response.text}")

        data = response.json()
        return self._parse_faster_whisper_result(data)

    def _parse_whisperx_result(self, data: dict) -> TranscriptionResult:
        """Parsed WhisperX API Antwort."""
        segments = []
        for seg in data.get("segments", []):
            words = []
            for w in seg.get("words", []) or []:
                words.append(Word(
                    word=w.get("word", ""),
                    start=w.get("start"),
                    end=w.get("end"),
                    score=w.get("score"),
                ))

            segments.append(Segment(
                start=seg.get("start", 0),
                end=seg.get("end", 0),
                text=seg.get("text", "").strip(),
                words=words,
                speaker=seg.get("speaker"),
            ))

        return TranscriptionResult(
            text=data.get("text", ""),
            segments=segments,
            language=data.get("language", "unknown"),
            duration=data.get("duration", 0),
            word_count=data.get("word_count", 0),
            has_word_timestamps=data.get("has_word_timestamps", False),
            has_diarization=data.get("has_diarization", False),
            source="whisperx",
        )

    def _parse_faster_whisper_result(self, data: dict) -> TranscriptionResult:
        """Parsed faster-whisper API Antwort."""
        segments = []
        for seg in data.get("segments", []):
            segments.append(Segment(
                start=seg.get("start", 0),
                end=seg.get("end", 0),
                text=seg.get("text", "").strip(),
                words=[],
                speaker=None,
            ))

        return TranscriptionResult(
            text=data.get("text", ""),
            segments=segments,
            language=data.get("language", "unknown"),
            duration=data.get("duration", 0),
            word_count=sum(len(s.text.split()) for s in segments),
            has_word_timestamps=False,
            has_diarization=False,
            source="faster-whisper",
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Singleton Client
_client: Optional[WhisperXClient] = None


def get_client() -> WhisperXClient:
    """Holt den Default-Client."""
    global _client
    if _client is None:
        _client = WhisperXClient()
    return _client


def transcribe(audio_path: str, language: str = None) -> TranscriptionResult:
    """
    Convenience-Funktion zum Transkribieren.

    Args:
        audio_path: Pfad zur Audiodatei
        language: Sprache (optional)

    Returns:
        TranscriptionResult
    """
    return get_client().transcribe(audio_path, language)


def is_audio_file(filepath: Path) -> bool:
    """Prüft ob Datei ein Audio-Format ist."""
    return filepath.suffix.lower() in AUDIO_EXTENSIONS


def is_video_file(filepath: Path) -> bool:
    """Prüft ob Datei ein Video-Format ist."""
    return filepath.suffix.lower() in VIDEO_EXTENSIONS


def is_transcribable(filepath: Path) -> bool:
    """Prüft ob Datei transkribiert werden kann."""
    return is_audio_file(filepath) or is_video_file(filepath)


# =============================================================================
# MAIN (Test)
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python whisperx_client.py <audio_file>")
        sys.exit(1)

    audio_path = sys.argv[1]
    print(f"Transcribing: {audio_path}")

    client = WhisperXClient()
    print(f"Using WhisperX: {client.use_whisperx}")

    try:
        result = client.transcribe(audio_path)

        print(f"\nLanguage: {result.language}")
        print(f"Duration: {result.duration:.1f}s")
        print(f"Words: {result.word_count}")
        print(f"Word Timestamps: {result.has_word_timestamps}")
        print(f"Diarization: {result.has_diarization}")
        print(f"Source: {result.source}")

        print(f"\n--- Searchable Text ---")
        print(result.to_searchable_text()[:1000])

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
