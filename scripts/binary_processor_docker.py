"""
Neural Vault - Docker-Basierter Binary File Processor
======================================================

Alle Verarbeitung läuft über Docker-Container für Linux-Portabilität.

Docker-Services:
- conductor-whisper (Port 9001): Audio→Text Transkription
- conductor-ffmpeg: Video/Audio Metadaten & Thumbnails
- conductor-paddleocr (Port 8866): Bild→Text OCR
- conductor-tika (Port 9998): Dokument-Extraktion (bereits vorhanden)

Technologien (Benchmarks Dezember 2025):
- faster-whisper (WER 6-7%)
- FFmpeg 7/8 (Standard)
- PaddleOCR (96.6% Genauigkeit)
"""

import os
import json
import subprocess
import tempfile
import requests
import base64
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, List, Any
from datetime import datetime
import time

# =============================================================================
# KONFIGURATION - Docker Container URLs
# =============================================================================

# Diese URLs muessen zu den Docker-Containern zeigen
WHISPER_URL = os.environ.get("WHISPER_URL", "http://localhost:9001")
FFMPEG_CONTAINER = os.environ.get("FFMPEG_CONTAINER", "conductor-ffmpeg")
PADDLEOCR_URL = os.environ.get("PADDLEOCR_URL", "http://localhost:8866")
TIKA_URL = os.environ.get("TIKA_URL", "http://localhost:9998")

# Pfad-Mapping: Lokaler Pfad → Container-Pfad
# Windows: F:/ → /mnt/data
from config.paths import BASE_DIR

# Windows: F:/ → /mnt/data
# Defaulting to drive root of BASE_DIR or just "F:/" if not easily determinable, but let's be smart.
default_host_path = os.path.splitdrive(BASE_DIR)[0] + "/" if os.name == 'nt' else "/"
HOST_DATA_PATH = Path(os.environ.get("HOST_DATA_PATH", default_host_path))
CONTAINER_DATA_PATH = os.environ.get("CONTAINER_DATA_PATH", "/mnt/data")


def host_to_container_path(host_path: Path) -> str:
    """Konvertiere Host-Pfad zu Container-Pfad."""
    rel_path = host_path.relative_to(HOST_DATA_PATH)
    return f"{CONTAINER_DATA_PATH}/{rel_path.as_posix()}"


@dataclass
class BinaryProcessingResult:
    """Ergebnis der Docker-basierten Binaerdatei-Verarbeitung."""
    filepath: str
    filename: str
    extension: str
    processing_type: str
    success: bool = False
    
    extracted_text: str = ""
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    thumbnail_path: Optional[str] = None
    
    file_listing: List[str] = field(default_factory=list)
    total_files: int = 0
    total_size_mb: float = 0.0
    
    duration_seconds: float = 0.0
    transcription: str = ""
    
    error: str = ""
    processing_time: float = 0.0
    docker_service: str = ""


# =============================================================================
# WHISPER DOCKER SERVICE (Audio Transkription)
# =============================================================================

def transcribe_audio_docker(filepath: Path) -> BinaryProcessingResult:
    """
    Transkribiere Audio via faster-whisper Docker Container.
    Container: fedirz/faster-whisper-server
    API: OpenAI-kompatibel
    """
    start = time.time()
    
    result = BinaryProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processing_type="audio_transcription",
        docker_service="conductor-whisper"
    )
    
    try:
        # Lese Datei als Binary
        with open(filepath, "rb") as f:
            files = {"file": (filepath.name, f, "audio/mpeg")}
            
            response = requests.post(
                f"{WHISPER_URL}/v1/audio/transcriptions",
                files=files,
                data={
                    "model": "Systran/faster-whisper-base",
                    "language": "de",
                    "response_format": "json"
                },
                timeout=300  # 5 Minuten fuer lange Audios
            )
        
        if response.ok:
            data = response.json()
            result.transcription = data.get("text", "")
            result.extracted_text = result.transcription
            result.metadata = {
                "language": data.get("language", "unknown"),
                "duration": data.get("duration", 0),
                "model": "faster-whisper-base"
            }
            result.summary = f"Transkription: {len(result.transcription.split())} Wörter"
            result.success = True
        else:
            result.error = f"Whisper API Fehler: {response.status_code} - {response.text[:200]}"
            
    except requests.exceptions.ConnectionError:
        result.error = f"Keine Verbindung zu Whisper Container ({WHISPER_URL})"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# FFMPEG DOCKER SERVICE (Video/Audio Metadaten)
# =============================================================================

def process_video_docker(filepath: Path, generate_thumbnail: bool = True) -> BinaryProcessingResult:
    """
    Extrahiere Video-Metadaten via FFmpeg Docker Container.
    Container: jrottenberg/ffmpeg (läuft als persistent container)
    """
    start = time.time()
    
    result = BinaryProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processing_type="video",
        docker_service="conductor-ffmpeg"
    )
    
    try:
        # Container-Pfad
        container_path = host_to_container_path(filepath)
        
        # FFprobe im Container ausführen
        cmd = [
            "docker", "exec", FFMPEG_CONTAINER,
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            container_path
        ]
        
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if proc.returncode != 0:
            result.error = f"FFprobe Fehler: {proc.stderr[:200]}"
            result.processing_time = time.time() - start
            return result
        
        metadata = json.loads(proc.stdout)
        format_info = metadata.get("format", {})
        streams = metadata.get("streams", [])
        
        duration = float(format_info.get("duration", 0))
        result.duration_seconds = duration
        
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
        
        result.metadata = {
            "duration": duration,
            "duration_formatted": f"{int(duration//60)}:{int(duration%60):02d}",
            "format": format_info.get("format_name"),
            "size_bytes": int(format_info.get("size", 0)),
            "video": {
                "codec": video_stream.get("codec_name"),
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
            },
            "audio": {
                "codec": audio_stream.get("codec_name"),
                "sample_rate": audio_stream.get("sample_rate"),
            }
        }
        
        width = video_stream.get("width", "?")
        height = video_stream.get("height", "?")
        result.summary = f"Video {width}x{height}, {int(duration//60)}:{int(duration%60):02d}"
        
        # Thumbnail generieren (optional)
        if generate_thumbnail and duration > 0:
            thumb_time = min(10, duration / 2)
            thumb_container_path = f"/tmp/ffmpeg/{filepath.stem}_thumb.jpg"
            
            thumb_cmd = [
                "docker", "exec", FFMPEG_CONTAINER,
                "ffmpeg", "-y",
                "-i", container_path,
                "-ss", str(thumb_time),
                "-vframes", "1",
                "-q:v", "5",
                thumb_container_path
            ]
            
            thumb_proc = subprocess.run(thumb_cmd, capture_output=True, timeout=30)
            
            if thumb_proc.returncode == 0:
                result.thumbnail_path = thumb_container_path
                result.metadata["thumbnail"] = thumb_container_path
        
        result.success = True
        
    except subprocess.TimeoutExpired:
        result.error = "Timeout bei Video-Analyse"
    except json.JSONDecodeError:
        result.error = "Ungueltige FFprobe Ausgabe"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


def process_audio_docker(filepath: Path, transcribe: bool = True) -> BinaryProcessingResult:
    """
    Verarbeite Audio: Metadaten via FFmpeg, Optional Transkription via Whisper.
    """
    # Erst Metadaten via FFmpeg
    result = process_video_docker(filepath, generate_thumbnail=False)
    result.processing_type = "audio"
    
    # Dann Transkription
    if transcribe:
        trans_result = transcribe_audio_docker(filepath)
        if trans_result.success:
            result.transcription = trans_result.transcription
            result.extracted_text = trans_result.extracted_text
            result.metadata["transcription"] = {
                "text": trans_result.transcription[:500],
                "word_count": len(trans_result.transcription.split())
            }
    
    return result


# =============================================================================
# PADDLEOCR DOCKER SERVICE (Bild OCR)
# =============================================================================

def process_image_ocr_docker(filepath: Path) -> BinaryProcessingResult:
    """
    OCR für Bilder via PaddleOCR Docker Container.
    Container: paddlecloud/paddleocr
    """
    start = time.time()
    
    result = BinaryProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processing_type="image_ocr",
        docker_service="conductor-paddleocr"
    )
    
    try:
        # Lese Bild als Base64
        with open(filepath, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # PaddleOCR API Call
        response = requests.post(
            f"{PADDLEOCR_URL}/predict",
            json={
                "image": image_data,
                "lang": "german"
            },
            timeout=60
        )
        
        if response.ok:
            data = response.json()
            
            # Extrahiere Text aus Ergebnis
            text_lines = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, list) and len(item) > 1:
                        text_lines.append(item[1][0] if isinstance(item[1], list) else str(item[1]))
            elif isinstance(data, dict):
                text_lines = data.get("texts", [])
            
            result.extracted_text = "\n".join(text_lines)
            result.summary = f"OCR: {len(text_lines)} Zeilen erkannt"
            result.metadata = {
                "ocr_engine": "paddleocr-docker",
                "lines": len(text_lines),
                "char_count": len(result.extracted_text)
            }
            result.success = True
        else:
            result.error = f"PaddleOCR API Fehler: {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        result.error = f"Keine Verbindung zu PaddleOCR Container ({PADDLEOCR_URL})"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# TIKA DOCKER SERVICE (Archive & Dokumente)
# =============================================================================

def process_archive_via_tika(filepath: Path) -> BinaryProcessingResult:
    """
    Für Archive: Nutze Tika's Recursive Parser.
    Container: apache/tika (bereits vorhanden)
    """
    start = time.time()
    
    result = BinaryProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processing_type="archive",
        docker_service="conductor-tika"
    )
    
    try:
        with open(filepath, "rb") as f:
            # Tika mit Recursive Metadata Extraktion
            response = requests.put(
                f"{TIKA_URL}/rmeta/text",
                data=f,
                headers={"Accept": "application/json"},
                timeout=120
            )
        
        if response.ok:
            items = response.json()
            
            file_list = []
            for item in items:
                name = item.get("resourceName", item.get("X-TIKA:embedded_resource_path", ""))
                if name:
                    file_list.append(name)
            
            result.file_listing = file_list[:50]
            result.total_files = len(file_list)
            result.summary = f"Archiv mit {len(file_list)} Dateien"
            result.metadata = {
                "files": file_list[:20],
                "total": len(file_list)
            }
            result.success = True
        else:
            result.error = f"Tika Fehler: {response.status_code}"
            
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# MAIN DISPATCHER
# =============================================================================

ARCHIVE_EXTENSIONS = {'.7z', '.zip', '.rar', '.tar', '.gz', '.bz2', '.xz'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}


def process_binary_file_docker(filepath: Path, transcribe_audio: bool = True) -> BinaryProcessingResult:
    """
    Hauptfunktion: Verarbeite Binärdatei über Docker-Container.
    
    Args:
        filepath: Pfad zur Datei
        transcribe_audio: Wenn True, transkribiere Audio via Whisper
    
    Returns:
        BinaryProcessingResult mit extrahierten Informationen
    """
    ext = filepath.suffix.lower()
    
    if ext in ARCHIVE_EXTENSIONS:
        return process_archive_via_tika(filepath)
    elif ext in VIDEO_EXTENSIONS:
        return process_video_docker(filepath)
    elif ext in AUDIO_EXTENSIONS:
        return process_audio_docker(filepath, transcribe=transcribe_audio)
    elif ext in IMAGE_EXTENSIONS:
        return process_image_ocr_docker(filepath)
    else:
        return BinaryProcessingResult(
            filepath=str(filepath),
            filename=filepath.name,
            extension=ext,
            processing_type="unknown",
            error=f"Kein Docker-Processor für {ext}"
        )


def check_docker_services() -> Dict[str, bool]:
    """Prüfe welche Docker-Services verfügbar sind."""
    services = {}
    
    # Whisper
    try:
        r = requests.get(f"{WHISPER_URL}/health", timeout=5)
        services["whisper"] = r.ok
    except:
        services["whisper"] = False
    
    # FFmpeg Container
    try:
        proc = subprocess.run(
            ["docker", "exec", FFMPEG_CONTAINER, "ffmpeg", "-version"],
            capture_output=True, timeout=10
        )
        services["ffmpeg"] = proc.returncode == 0
    except:
        services["ffmpeg"] = False
    
    # PaddleOCR
    try:
        r = requests.get(f"{PADDLEOCR_URL}/health", timeout=5)
        services["paddleocr"] = r.ok
    except:
        services["paddleocr"] = False
    
    # Tika
    try:
        r = requests.get(f"{TIKA_URL}", timeout=5)
        services["tika"] = r.ok
    except:
        services["tika"] = False
    
    return services


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("NEURAL VAULT - DOCKER BINARY PROCESSOR")
    print("=" * 60)
    
    print("\nDocker-Services Status:")
    services = check_docker_services()
    for name, status in services.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
    
    print(f"\nKonfiguration:")
    print(f"  WHISPER_URL: {WHISPER_URL}")
    print(f"  PADDLEOCR_URL: {PADDLEOCR_URL}")
    print(f"  TIKA_URL: {TIKA_URL}")
    print(f"  FFMPEG_CONTAINER: {FFMPEG_CONTAINER}")
    
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        if test_file.exists():
            print(f"\nTeste: {test_file}")
            result = process_binary_file_docker(test_file)
            print(json.dumps(asdict(result), indent=2, default=str))
