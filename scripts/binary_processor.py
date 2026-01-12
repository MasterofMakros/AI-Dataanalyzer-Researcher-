"""
Neural Vault - Binary File Processor
=====================================

Verarbeitet Dateitypen die Tika nicht gut handhaben kann:
- Archive: 7z, zip, rar → Inhaltsverzeichnis
- Videos: mp4, avi, mkv → Thumbnails + Audio-Transkription
- Audio: mp3, wav, aac → Transkription via Whisper
- 3D-Modelle: blend, fbx, obj → Metadaten
- Bilder ohne Text: jpg, png → OCR via Surya/PaddleOCR

Technologien basierend auf Benchmarks Dezember 2025:
- FFmpeg 8.0 für Video/Audio
- faster-whisper (WER 6-7%, 4x schneller)
- Surya OCR (97.7% Genauigkeit)
- 7-Zip CLI für Archive
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, List, Any
from datetime import datetime

# Konfiguration
FFMPEG_PATH = "ffmpeg"  # Muss im PATH sein
FFPROBE_PATH = "ffprobe"
SEVENZ_PATH = "7z"  # 7-Zip CLI

# URLs (falls Container-basiert)
WHISPER_URL = "http://localhost:9000"  # Optional: Whisper Container
SURYA_URL = "http://localhost:8866"    # Optional: Surya Container


@dataclass
class BinaryProcessingResult:
    """Ergebnis der Binaerdatei-Verarbeitung."""
    filepath: str
    filename: str
    extension: str
    processing_type: str  # archive, video, audio, image, 3d_model
    success: bool = False
    
    # Extrahierte Informationen
    extracted_text: str = ""
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    thumbnail_path: Optional[str] = None
    
    # Fuer Archive
    file_listing: List[str] = field(default_factory=list)
    total_files: int = 0
    total_size_mb: float = 0.0
    
    # Fuer Video/Audio
    duration_seconds: float = 0.0
    transcription: str = ""
    
    # Fehler
    error: str = ""
    processing_time: float = 0.0


# =============================================================================
# ARCHIVE PROCESSING (7-Zip)
# =============================================================================

def process_archive(filepath: Path) -> BinaryProcessingResult:
    """
    Extrahiere Inhaltsverzeichnis aus Archiven.
    Unterstuetzte Formate: 7z, zip, rar, tar, gz, bz2
    """
    import time
    start = time.time()
    
    result = BinaryProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processing_type="archive"
    )
    
    try:
        # 7z l = Liste Inhalt
        cmd = [SEVENZ_PATH, "l", "-slt", str(filepath)]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace"
        )
        
        if proc.returncode != 0:
            result.error = f"7z Fehler: {proc.stderr[:200]}"
            result.processing_time = time.time() - start
            return result
        
        # Parse Output
        files = []
        current_file = {}
        total_size = 0
        
        for line in proc.stdout.split("\n"):
            line = line.strip()
            if line.startswith("Path = "):
                if current_file and "Path" in current_file:
                    files.append(current_file)
                current_file = {"Path": line[7:]}
            elif line.startswith("Size = "):
                try:
                    size = int(line[7:])
                    current_file["Size"] = size
                    total_size += size
                except:
                    pass
            elif line.startswith("Modified = "):
                current_file["Modified"] = line[11:]
        
        if current_file and "Path" in current_file:
            files.append(current_file)
        
        # Ergebnisse
        result.file_listing = [f["Path"] for f in files[:50]]  # Max 50
        result.total_files = len(files)
        result.total_size_mb = total_size / (1024 * 1024)
        result.success = True
        
        # Zusammenfassung generieren
        extensions = {}
        for f in files:
            ext = Path(f["Path"]).suffix.lower() or "[no_ext]"
            extensions[ext] = extensions.get(ext, 0) + 1
        
        top_exts = sorted(extensions.items(), key=lambda x: -x[1])[:5]
        ext_summary = ", ".join([f"{e[0]}({e[1]})" for e in top_exts])
        
        result.summary = f"Archiv mit {len(files)} Dateien ({result.total_size_mb:.1f}MB). Typen: {ext_summary}"
        result.extracted_text = "\n".join(result.file_listing[:20])
        
        result.metadata = {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "extensions": dict(extensions),
            "top_files": [f["Path"] for f in files[:10]]
        }
        
    except subprocess.TimeoutExpired:
        result.error = "Timeout beim Archiv-Scan"
    except FileNotFoundError:
        result.error = "7z nicht gefunden - bitte installieren"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# VIDEO PROCESSING (FFmpeg + FFprobe)
# =============================================================================

def process_video(filepath: Path, generate_thumbnail: bool = True) -> BinaryProcessingResult:
    """
    Extrahiere Metadaten und optionalen Thumbnail aus Videos.
    """
    import time
    start = time.time()
    
    result = BinaryProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processing_type="video"
    )
    
    try:
        # FFprobe fuer Metadaten
        cmd = [
            FFPROBE_PATH,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(filepath)
        ]
        
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if proc.returncode != 0:
            result.error = f"FFprobe Fehler: {proc.stderr[:200]}"
            result.processing_time = time.time() - start
            return result
        
        metadata = json.loads(proc.stdout)
        
        # Extrahiere wichtige Infos
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
            "bitrate": int(format_info.get("bit_rate", 0)),
            "video": {
                "codec": video_stream.get("codec_name"),
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "fps": video_stream.get("r_frame_rate")
            },
            "audio": {
                "codec": audio_stream.get("codec_name"),
                "sample_rate": audio_stream.get("sample_rate"),
                "channels": audio_stream.get("channels")
            }
        }
        
        # Zusammenfassung
        width = video_stream.get("width", "?")
        height = video_stream.get("height", "?")
        result.summary = f"Video {width}x{height}, {int(duration//60)}:{int(duration%60):02d}, {video_stream.get('codec_name', 'unknown')}"
        
        # Thumbnail generieren
        if generate_thumbnail and duration > 0:
            thumb_time = min(10, duration / 2)  # Mitte oder 10s
            thumb_path = filepath.parent / f".thumb_{filepath.stem}.jpg"
            
            thumb_cmd = [
                FFMPEG_PATH,
                "-y",
                "-i", str(filepath),
                "-ss", str(thumb_time),
                "-vframes", "1",
                "-q:v", "5",
                str(thumb_path)
            ]
            
            thumb_proc = subprocess.run(
                thumb_cmd,
                capture_output=True,
                timeout=30
            )
            
            if thumb_proc.returncode == 0 and thumb_path.exists():
                result.thumbnail_path = str(thumb_path)
        
        result.success = True
        
    except subprocess.TimeoutExpired:
        result.error = "Timeout bei Video-Analyse"
    except FileNotFoundError:
        result.error = "FFmpeg/FFprobe nicht gefunden"
    except json.JSONDecodeError:
        result.error = "Ungueltige FFprobe Ausgabe"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# AUDIO PROCESSING (Extract + Whisper)
# =============================================================================

def process_audio(filepath: Path, transcribe: bool = True) -> BinaryProcessingResult:
    """
    Extrahiere Metadaten und optionale Transkription aus Audio.
    Nutzt faster-whisper falls verfuegbar.
    """
    import time
    start = time.time()
    
    result = BinaryProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processing_type="audio"
    )
    
    try:
        # FFprobe fuer Metadaten (wie bei Video)
        cmd = [
            FFPROBE_PATH,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(filepath)
        ]
        
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if proc.returncode == 0:
            metadata = json.loads(proc.stdout)
            format_info = metadata.get("format", {})
            audio_stream = next(
                (s for s in metadata.get("streams", []) if s.get("codec_type") == "audio"),
                {}
            )
            
            duration = float(format_info.get("duration", 0))
            result.duration_seconds = duration
            
            result.metadata = {
                "duration": duration,
                "duration_formatted": f"{int(duration//60)}:{int(duration%60):02d}",
                "format": format_info.get("format_name"),
                "codec": audio_stream.get("codec_name"),
                "sample_rate": audio_stream.get("sample_rate"),
                "channels": audio_stream.get("channels"),
                "bitrate": format_info.get("bit_rate")
            }
            
            result.summary = f"Audio {int(duration//60)}:{int(duration%60):02d}, {audio_stream.get('codec_name', 'unknown')}"
        
        # Transkription mit faster-whisper (falls installiert)
        if transcribe:
            try:
                from faster_whisper import WhisperModel
                
                model = WhisperModel("base", device="auto", compute_type="auto")
                segments, info = model.transcribe(str(filepath), beam_size=5)
                
                transcription = " ".join([seg.text for seg in segments])
                result.transcription = transcription
                result.extracted_text = transcription
                result.metadata["language"] = info.language
                result.metadata["language_probability"] = info.language_probability
                
            except ImportError:
                result.metadata["transcription_note"] = "faster-whisper nicht installiert"
            except Exception as e:
                result.metadata["transcription_error"] = str(e)
        
        result.success = True
        
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# 3D MODEL PROCESSING (trimesh)
# =============================================================================

def process_3d_model(filepath: Path) -> BinaryProcessingResult:
    """
    Extrahiere Metadaten aus 3D-Modellen.
    Unterstuetzte Formate: obj, stl, ply, gltf, glb
    """
    import time
    start = time.time()
    
    result = BinaryProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processing_type="3d_model"
    )
    
    try:
        import trimesh
        
        mesh = trimesh.load(str(filepath))
        
        if isinstance(mesh, trimesh.Scene):
            # Scene mit mehreren Objekten
            geometries = list(mesh.geometry.values())
            total_vertices = sum(g.vertices.shape[0] for g in geometries if hasattr(g, 'vertices'))
            total_faces = sum(g.faces.shape[0] for g in geometries if hasattr(g, 'faces'))
            
            result.metadata = {
                "type": "scene",
                "object_count": len(geometries),
                "total_vertices": total_vertices,
                "total_faces": total_faces,
                "objects": list(mesh.geometry.keys())[:20]
            }
            result.summary = f"3D Scene mit {len(geometries)} Objekten, {total_vertices} Vertices"
            
        elif hasattr(mesh, 'vertices'):
            # Einzelnes Mesh
            result.metadata = {
                "type": "mesh",
                "vertices": mesh.vertices.shape[0],
                "faces": mesh.faces.shape[0] if hasattr(mesh, 'faces') else 0,
                "bounds": mesh.bounds.tolist() if hasattr(mesh, 'bounds') else None,
                "is_watertight": mesh.is_watertight if hasattr(mesh, 'is_watertight') else None,
                "volume": float(mesh.volume) if hasattr(mesh, 'volume') and mesh.is_watertight else None
            }
            result.summary = f"3D Mesh mit {mesh.vertices.shape[0]} Vertices, {result.metadata['faces']} Faces"
        
        result.success = True
        
    except ImportError:
        result.error = "trimesh nicht installiert: pip install trimesh"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# IMAGE OCR (Surya oder PaddleOCR Fallback)
# =============================================================================

def process_image_ocr(filepath: Path) -> BinaryProcessingResult:
    """
    OCR fuer Bilder mit Surya (bevorzugt) oder PaddleOCR.
    """
    import time
    start = time.time()
    
    result = BinaryProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processing_type="image_ocr"
    )
    
    # Versuche Surya (beste Genauigkeit: 97.7%)
    try:
        from surya.ocr import run_ocr
        from surya.model.detection import segformer
        from surya.model.recognition.model import load_model
        from surya.model.recognition.processor import load_processor
        from PIL import Image
        
        image = Image.open(filepath)
        
        det_model, det_processor = segformer.load_model(), segformer.load_processor()
        rec_model, rec_processor = load_model(), load_processor()
        
        predictions = run_ocr(
            [image],
            [["de", "en"]],
            det_model,
            det_processor,
            rec_model,
            rec_processor
        )
        
        text_lines = [line.text for page in predictions for line in page.text_lines]
        result.extracted_text = "\n".join(text_lines)
        result.summary = f"OCR (Surya): {len(text_lines)} Zeilen erkannt"
        result.metadata = {"ocr_engine": "surya", "lines": len(text_lines)}
        result.success = True
        
        result.processing_time = time.time() - start
        return result
        
    except ImportError:
        pass  # Surya nicht verfuegbar, versuche PaddleOCR
    except Exception as e:
        result.metadata["surya_error"] = str(e)
    
    # Fallback: PaddleOCR (96.6% Genauigkeit)
    try:
        from paddleocr import PaddleOCR
        
        ocr = PaddleOCR(use_angle_cls=True, lang='german')
        paddle_result = ocr.ocr(str(filepath), cls=True)
        
        text_lines = []
        for page in paddle_result:
            if page:
                for line in page:
                    text_lines.append(line[1][0])
        
        result.extracted_text = "\n".join(text_lines)
        result.summary = f"OCR (PaddleOCR): {len(text_lines)} Zeilen erkannt"
        result.metadata = {"ocr_engine": "paddleocr", "lines": len(text_lines)}
        result.success = True
        
    except ImportError:
        result.error = "Kein OCR-Engine verfuegbar. Installieren: pip install paddleocr"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# MAIN DISPATCHER
# =============================================================================

# Dateityp-Mappings
ARCHIVE_EXTENSIONS = {'.7z', '.zip', '.rar', '.tar', '.gz', '.bz2', '.xz', '.cab'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.wma'}
MODEL_3D_EXTENSIONS = {'.obj', '.stl', '.ply', '.gltf', '.glb', '.fbx', '.3ds', '.blend'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}


def process_binary_file(filepath: Path) -> BinaryProcessingResult:
    """
    Hauptfunktion: Erkennt Dateityp und waehlt passenden Processor.
    """
    ext = filepath.suffix.lower()
    
    if ext in ARCHIVE_EXTENSIONS:
        return process_archive(filepath)
    elif ext in VIDEO_EXTENSIONS:
        return process_video(filepath)
    elif ext in AUDIO_EXTENSIONS:
        return process_audio(filepath)
    elif ext in MODEL_3D_EXTENSIONS:
        return process_3d_model(filepath)
    elif ext in IMAGE_EXTENSIONS:
        return process_image_ocr(filepath)
    else:
        # Unbekannter Typ
        return BinaryProcessingResult(
            filepath=str(filepath),
            filename=filepath.name,
            extension=ext,
            processing_type="unknown",
            error=f"Kein Processor fuer {ext}"
        )


def is_binary_processable(filepath: Path) -> bool:
    """Pruefe ob Datei von diesem Modul verarbeitet werden kann."""
    ext = filepath.suffix.lower()
    return ext in (
        ARCHIVE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS |
        MODEL_3D_EXTENSIONS | IMAGE_EXTENSIONS
    )


# =============================================================================
# CLI / TEST
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("NEURAL VAULT - BINARY FILE PROCESSOR")
    print("=" * 60)
    
    # Check verfuegbare Tools
    print("\nVerfuegbare Tools:")
    
    # 7z
    try:
        subprocess.run([SEVENZ_PATH], capture_output=True, timeout=5)
        print("  ✅ 7-Zip (Archive)")
    except:
        print("  ❌ 7-Zip nicht gefunden")
    
    # FFmpeg
    try:
        subprocess.run([FFMPEG_PATH, "-version"], capture_output=True, timeout=5)
        print("  ✅ FFmpeg (Video/Audio)")
    except:
        print("  ❌ FFmpeg nicht gefunden")
    
    # trimesh
    try:
        import trimesh
        print("  ✅ trimesh (3D-Modelle)")
    except:
        print("  ❌ trimesh nicht installiert")
    
    # OCR
    try:
        from paddleocr import PaddleOCR
        print("  ✅ PaddleOCR (Bilder)")
    except:
        print("  ❌ PaddleOCR nicht installiert")
    
    try:
        from faster_whisper import WhisperModel
        print("  ✅ faster-whisper (Audio-Transkription)")
    except:
        print("  ❌ faster-whisper nicht installiert")
    
    print("\n" + "=" * 60)
    
    # Test mit Argument
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        if test_file.exists():
            print(f"\nTeste: {test_file}")
            result = process_binary_file(test_file)
            print(json.dumps(asdict(result), indent=2, default=str))
