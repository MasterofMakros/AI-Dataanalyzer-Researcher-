"""
Neural Vault - Extended File Type Processor
============================================

Erweitert die Dateiverarbeitung um bisher nicht unterstützte Typen.
Basierend auf F: Laufwerk Analyse (27.12.2025):

P0 - Kritisch:
- .torrent (94,568 Dateien) → bencode2
- .eml (65,960 Dateien) → eml-parser

P1 - Hoch:
- .exr (4,526 Dateien) → OpenEXR
- .srt (4,646 Dateien) → Regex
- .fbx (3,217 Dateien) → pyassimp (falls verfügbar)
- .apk (1,573 Dateien) → ZIP + AndroidManifest

Qualitätsziele:
- Hohe Genauigkeit (keine Halluzinationen)
- Minimaler Informationsverlust
- Plausibilitätsprüfung der Ergebnisse
"""

import os
import re
import json
import zipfile
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import time


@dataclass
class ExtendedProcessingResult:
    """Ergebnis der erweiterten Dateiverarbeitung."""
    filepath: str
    filename: str
    extension: str
    file_type: str
    success: bool = False
    
    # Extrahierte Daten
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_text: str = ""
    summary: str = ""
    
    # Qualitätsmetriken
    completeness: float = 0.0  # 0-1: Wie vollständig sind die Daten
    confidence: float = 0.0    # 0-1: Vertrauen in die Extraktion
    
    error: str = ""
    processing_time: float = 0.0


# =============================================================================
# TORRENT PARSER (bencode2 - Dezember 2025)
# =============================================================================

def process_torrent(filepath: Path) -> ExtendedProcessingResult:
    """
    Extrahiere Metadaten aus .torrent Dateien.
    Nutzt bencode2 (Rust-Backend, schnell und korrekt).
    
    Extrahiert:
    - Name des Torrents
    - Dateigröße
    - Anzahl Dateien
    - Tracker URLs
    - Erstellungsdatum
    - Kommentar
    """
    start = time.time()
    
    result = ExtendedProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=".torrent",
        file_type="torrent"
    )
    
    try:
        import bencode2
        
        with open(filepath, "rb") as f:
            data = bencode2.bdecode(f.read())
        
        # Hauptinfo
        info = data.get(b"info", {})
        
        # Name
        name = info.get(b"name", b"").decode("utf-8", errors="replace")
        
        # Dateien und Größe
        files = info.get(b"files", [])
        if files:
            # Multi-File Torrent
            total_size = sum(f.get(b"length", 0) for f in files)
            file_count = len(files)
            file_list = []
            for f in files[:20]:  # Max 20 für Übersicht
                path_parts = f.get(b"path", [])
                path = "/".join(p.decode("utf-8", errors="replace") for p in path_parts)
                file_list.append(path)
        else:
            # Single-File Torrent
            total_size = info.get(b"length", 0)
            file_count = 1
            file_list = [name]
        
        # Tracker
        announce = data.get(b"announce", b"").decode("utf-8", errors="replace")
        announce_list = data.get(b"announce-list", [])
        trackers = [announce] if announce else []
        for tier in announce_list[:5]:
            for tracker in tier[:3]:
                if isinstance(tracker, bytes):
                    trackers.append(tracker.decode("utf-8", errors="replace"))
        
        # Erstellungsdatum
        creation_date = data.get(b"creation date")
        if creation_date:
            creation_date = datetime.fromtimestamp(creation_date).isoformat()
        
        # Kommentar
        comment = data.get(b"comment", b"")
        if isinstance(comment, bytes):
            comment = comment.decode("utf-8", errors="replace")
        
        # Created By
        created_by = data.get(b"created by", b"")
        if isinstance(created_by, bytes):
            created_by = created_by.decode("utf-8", errors="replace")
        
        result.metadata = {
            "name": name,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "files": file_list,
            "trackers": trackers[:5],
            "creation_date": creation_date,
            "comment": comment,
            "created_by": created_by
        }
        
        result.extracted_text = f"Torrent: {name}\nDateien: {file_count}\nGröße: {result.metadata['total_size_mb']}MB"
        result.summary = f"Torrent '{name}' mit {file_count} Dateien ({result.metadata['total_size_mb']}MB)"
        result.success = True
        result.completeness = 0.9 if name and total_size else 0.5
        result.confidence = 1.0  # Bencode ist deterministisch
        
    except ImportError:
        result.error = "bencode2 nicht installiert: pip install bencode2"
    except Exception as e:
        result.error = str(e)
        result.completeness = 0.0
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# EML PARSER (eml-parser - Mai 2025)
# =============================================================================

def process_eml(filepath: Path) -> ExtendedProcessingResult:
    """
    Extrahiere Metadaten und Inhalt aus .eml E-Mail Dateien.
    
    Extrahiert:
    - From, To, CC, BCC
    - Subject
    - Date
    - Body (Text und HTML)
    - Attachments (Namen)
    - Headers
    """
    start = time.time()
    
    result = ExtendedProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=".eml",
        file_type="email"
    )
    
    try:
        import eml_parser
        
        with open(filepath, "rb") as f:
            raw_email = f.read()
        
        ep = eml_parser.EmlParser()
        parsed = ep.decode_email_bytes(raw_email)
        
        header = parsed.get("header", {})
        body = parsed.get("body", [])
        
        # Extrahiere Header-Infos
        from_addr = header.get("from", "")
        to_addrs = header.get("to", [])
        cc_addrs = header.get("cc", [])
        subject = header.get("subject", "")
        date = header.get("date")
        if date:
            date = date.isoformat() if hasattr(date, "isoformat") else str(date)
        
        # Body Text
        body_text = ""
        body_html = ""
        for part in body:
            content = part.get("content", "")
            if part.get("content_type", "").startswith("text/plain"):
                body_text = content
            elif part.get("content_type", "").startswith("text/html"):
                body_html = content
        
        # Attachments
        attachments = parsed.get("attachment", [])
        attachment_names = [a.get("filename", "unknown") for a in attachments]
        
        result.metadata = {
            "from": from_addr,
            "to": to_addrs[:10] if isinstance(to_addrs, list) else [to_addrs],
            "cc": cc_addrs[:10] if isinstance(cc_addrs, list) else [],
            "subject": subject,
            "date": date,
            "attachment_count": len(attachments),
            "attachments": attachment_names[:10],
            "has_html": bool(body_html),
            "body_length": len(body_text or body_html)
        }
        
        # Text für Indexierung
        result.extracted_text = f"Von: {from_addr}\nAn: {', '.join(result.metadata['to'][:3])}\nBetreff: {subject}\n\n{body_text[:2000]}"
        result.summary = f"E-Mail von {from_addr}: '{subject}' ({len(attachments)} Anhänge)"
        result.success = True
        result.completeness = 0.9 if subject and from_addr else 0.6
        result.confidence = 1.0
        
    except ImportError:
        result.error = "eml-parser nicht installiert: pip install eml-parser"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# EXR PARSER (OpenEXR - November 2025 v3.4.4)
# =============================================================================

def process_exr(filepath: Path) -> ExtendedProcessingResult:
    """
    Extrahiere Metadaten aus OpenEXR Bilddateien (VFX-Standard).
    
    Extrahiert:
    - Bildgröße
    - Channels (RGB, Alpha, Depth, etc.)
    - Compression
    - Custom Metadata
    """
    start = time.time()
    
    result = ExtendedProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=".exr",
        file_type="exr_image"
    )
    
    try:
        import OpenEXR
        import Imath
        
        exr_file = OpenEXR.InputFile(str(filepath))
        header = exr_file.header()
        
        # Bildgröße
        dw = header.get("dataWindow")
        if dw:
            width = dw.max.x - dw.min.x + 1
            height = dw.max.y - dw.min.y + 1
        else:
            width = height = 0
        
        # Channels
        channels = list(header.get("channels", {}).keys())
        
        # Compression
        compression = str(header.get("compression", "unknown"))
        
        # Pixel Aspect Ratio
        pixel_aspect = float(header.get("pixelAspectRatio", 1.0))
        
        # Custom Metadata
        custom_meta = {}
        skip_keys = {"channels", "compression", "dataWindow", "displayWindow", 
                     "lineOrder", "pixelAspectRatio", "screenWindowCenter", 
                     "screenWindowWidth", "type"}
        for key, value in header.items():
            if key not in skip_keys:
                custom_meta[key] = str(value)[:100]
        
        result.metadata = {
            "width": width,
            "height": height,
            "channels": channels,
            "channel_count": len(channels),
            "compression": compression,
            "pixel_aspect_ratio": pixel_aspect,
            "custom_metadata": custom_meta
        }
        
        result.extracted_text = f"EXR {width}x{height}, {len(channels)} Channels: {', '.join(channels[:5])}"
        result.summary = f"EXR Bild {width}x{height}, {len(channels)} Channels"
        result.success = True
        result.completeness = 0.95
        result.confidence = 1.0
        
    except ImportError:
        result.error = "OpenEXR nicht installiert: pip install OpenEXR"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# SRT PARSER (Built-in Regex)
# =============================================================================

def process_srt(filepath: Path) -> ExtendedProcessingResult:
    """
    Extrahiere Untertitel-Text aus .srt Dateien.
    
    Extrahiert:
    - Anzahl Untertitel
    - Gesamtdauer
    - Vollständiger Text
    - Sprache (falls erkennbar)
    """
    start = time.time()
    
    result = ExtendedProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=".srt",
        file_type="subtitles"
    )
    
    try:
        # Versuche verschiedene Encodings
        content = None
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if not content:
            result.error = "Konnte Datei nicht lesen (Encoding-Problem)"
            return result
        
        # Parse SRT Format
        # 1
        # 00:00:01,000 --> 00:00:04,000
        # Text here
        
        pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\n((?:(?!\n\d+\n).)*)"
        matches = re.findall(pattern, content, re.DOTALL)
        
        subtitle_count = len(matches)
        all_text = []
        first_time = None
        last_time = None
        
        for idx, start_time, end_time, text in matches:
            all_text.append(text.strip())
            if first_time is None:
                first_time = start_time
            last_time = end_time
        
        full_text = " ".join(all_text)
        
        # Sprache erraten (sehr einfach)
        german_words = {"der", "die", "das", "und", "ist", "ein", "ich", "nicht", "du", "wir"}
        english_words = {"the", "and", "is", "you", "that", "to", "it", "for", "are", "was"}
        
        words = set(full_text.lower().split()[:100])
        german_score = len(words & german_words)
        english_score = len(words & english_words)
        
        if german_score > english_score:
            language = "de"
        elif english_score > german_score:
            language = "en"
        else:
            language = "unknown"
        
        result.metadata = {
            "subtitle_count": subtitle_count,
            "first_timestamp": first_time,
            "last_timestamp": last_time,
            "total_words": len(full_text.split()),
            "detected_language": language
        }
        
        result.extracted_text = full_text[:5000]  # Max 5000 Zeichen für Index
        result.summary = f"Untertitel: {subtitle_count} Einträge, {len(full_text.split())} Wörter ({language})"
        result.success = True
        result.completeness = 0.95 if subtitle_count > 0 else 0.3
        result.confidence = 0.9
        
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# APK PARSER (ZIP + AndroidManifest)
# =============================================================================

def process_apk(filepath: Path) -> ExtendedProcessingResult:
    """
    Extrahiere Metadaten aus Android APK Dateien.
    
    Extrahiert:
    - Package Name
    - Version
    - Permissions
    - Activities
    """
    start = time.time()
    
    result = ExtendedProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=".apk",
        file_type="android_app"
    )
    
    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            file_list = zf.namelist()
            
            # Dateien analysieren
            has_manifest = "AndroidManifest.xml" in file_list
            has_dex = any(f.endswith(".dex") for f in file_list)
            has_resources = "resources.arsc" in file_list
            
            # Zähle verschiedene Dateitypen
            extensions = {}
            for f in file_list:
                ext = Path(f).suffix.lower()
                extensions[ext] = extensions.get(ext, 0) + 1
            
            result.metadata = {
                "file_count": len(file_list),
                "has_manifest": has_manifest,
                "has_dex": has_dex,
                "has_resources": has_resources,
                "file_types": dict(sorted(extensions.items(), key=lambda x: -x[1])[:10]),
                "size_bytes": filepath.stat().st_size
            }
            
            # Package-Name aus Dateiname extrahieren
            pkg_match = re.match(r"([a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+)", filepath.stem.lower())
            if pkg_match:
                result.metadata["package_name"] = pkg_match.group(1)
            
            result.extracted_text = f"APK: {filepath.name}\nDateien: {len(file_list)}"
            result.summary = f"Android APK mit {len(file_list)} Dateien"
            result.success = True
            result.completeness = 0.6  # Ohne Manifest-Parsing eingeschränkt
            result.confidence = 0.8
            
    except zipfile.BadZipFile:
        result.error = "Ungültige ZIP/APK Datei"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# MSG PARSER (Outlook E-Mails)
# =============================================================================

def process_msg(filepath: Path) -> ExtendedProcessingResult:
    """
    Extrahiere Metadaten aus Outlook .msg Dateien.
    """
    start = time.time()
    
    result = ExtendedProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=".msg",
        file_type="outlook_email"
    )
    
    try:
        # Versuche extract_msg
        import extract_msg
        
        msg = extract_msg.Message(str(filepath))
        
        result.metadata = {
            "from": msg.sender,
            "to": msg.to,
            "cc": msg.cc,
            "subject": msg.subject,
            "date": str(msg.date) if msg.date else None,
            "attachment_count": len(msg.attachments)
        }
        
        body = msg.body or ""
        result.extracted_text = f"Von: {msg.sender}\nBetreff: {msg.subject}\n\n{body[:2000]}"
        result.summary = f"Outlook Mail von {msg.sender}: '{msg.subject}'"
        result.success = True
        result.completeness = 0.9
        result.confidence = 1.0
        
        msg.close()
        
    except ImportError:
        result.error = "extract-msg nicht installiert: pip install extract-msg"
    except Exception as e:
        result.error = str(e)
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# FBX/3D MODEL PARSER (trimesh - keine native DLLs nötig)
# =============================================================================

def process_fbx(filepath: Path) -> ExtendedProcessingResult:
    """
    Extrahiere Metadaten aus 3D-Modell Dateien.
    Nutzt trimesh (reine Python-Bibliothek, keine native DLLs nötig).
    
    Unterstützte Formate: .obj, .stl, .ply, .gltf, .glb
    FBX Support nur mit Assimp DLL (optional)
    
    Extrahiert:
    - Mesh-Statistiken (Vertices, Faces)
    - Bounding Box
    - Volumen (falls wasserdicht)
    """
    start = time.time()
    
    result = ExtendedProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        file_type="3d_model"
    )
    
    # Versuche trimesh zuerst (funktioniert ohne native DLLs)
    try:
        import trimesh
        
        mesh = trimesh.load(str(filepath))
        
        if isinstance(mesh, trimesh.Scene):
            # Scene mit mehreren Objekten
            geometries = list(mesh.geometry.values())
            mesh_count = len(geometries)
            total_vertices = sum(g.vertices.shape[0] for g in geometries if hasattr(g, 'vertices'))
            total_faces = sum(g.faces.shape[0] for g in geometries if hasattr(g, 'faces'))
            object_names = list(mesh.geometry.keys())[:10]
            
            result.metadata = {
                "mesh_count": mesh_count,
                "total_vertices": total_vertices,
                "total_faces": total_faces,
                "objects": object_names,
                "type": "scene"
            }
        elif hasattr(mesh, 'vertices'):
            # Einzelnes Mesh
            total_vertices = mesh.vertices.shape[0]
            total_faces = mesh.faces.shape[0] if hasattr(mesh, 'faces') else 0
            
            result.metadata = {
                "mesh_count": 1,
                "total_vertices": total_vertices,
                "total_faces": total_faces,
                "is_watertight": bool(mesh.is_watertight) if hasattr(mesh, 'is_watertight') else None,
                "type": "mesh"
            }
            
            # Bounding Box
            if hasattr(mesh, 'bounds') and mesh.bounds is not None:
                bounds = mesh.bounds
                result.metadata["bounds"] = {
                    "min": bounds[0].tolist(),
                    "max": bounds[1].tolist()
                }
        else:
            result.metadata = {"type": "unknown", "error": "Unbekanntes Mesh-Format"}
        
        result.extracted_text = f"3D-Modell: {result.metadata.get('mesh_count', 1)} Meshes, {result.metadata.get('total_vertices', 0)} Vertices"
        result.summary = f"3D-Modell ({filepath.suffix}): {result.metadata.get('total_vertices', 0)} Vertices, {result.metadata.get('total_faces', 0)} Faces"
        result.success = True
        result.completeness = 0.85
        result.confidence = 0.95
        
    except ImportError:
        result.error = "trimesh nicht installiert: pip install trimesh"
    except Exception as e:
        # Trimesh konnte Datei nicht laden, speichere trotzdem Basis-Info
        result.error = f"trimesh: {str(e)[:100]}"
        result.metadata = {"file_size": filepath.stat().st_size}
        result.summary = f"3D-Modell ({filepath.suffix}): Format nicht lesbar"
        result.completeness = 0.2
    
    result.processing_time = time.time() - start
    return result


# =============================================================================
# ARCHIVE PARSER (7-Zip Docker + Python tarfile)
# =============================================================================

def process_archive(filepath: Path) -> ExtendedProcessingResult:
    """
    Extrahiere Metadaten aus Archiven OHNE Entpacken.
    Nutzt 7-Zip Docker Container oder Python tarfile.
    
    Extrahiert:
    - Anzahl Dateien
    - Gesamtgröße (komprimiert/unkomprimiert)
    - Dateiliste
    - Kompressionstyp
    
    Spart Speicherplatz: Kein Entpacken auf Festplatte!
    """
    start = time.time()
    ext = filepath.suffix.lower()
    
    result = ExtendedProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=ext,
        file_type="archive"
    )
    
    try:
        # Python Built-in für .zip, .tar, .gz, .tar.gz
        if ext == ".zip":
            result = _process_zip(filepath, result)
        elif ext in [".tar", ".tgz"] or filepath.name.endswith(".tar.gz"):
            result = _process_tar(filepath, result)
        elif ext == ".gz" and not filepath.name.endswith(".tar.gz"):
            result = _process_gzip(filepath, result)
        else:
            # 7-Zip Docker für .rar, .7z und andere
            result = _process_with_7zip(filepath, result)
            
    except Exception as e:
        result.error = str(e)[:200]
    
    result.processing_time = time.time() - start
    return result


def _process_zip(filepath: Path, result: ExtendedProcessingResult) -> ExtendedProcessingResult:
    """ZIP-Archiv mit Python zipfile (kein Entpacken)."""
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            files = zf.namelist()
            infos = zf.infolist()
            
            total_size = sum(i.file_size for i in infos)
            compressed_size = sum(i.compress_size for i in infos)
            
            result.success = True
            result.metadata = {
                "file_count": len(files),
                "total_size_bytes": total_size,
                "compressed_size_bytes": compressed_size,
                "compression_ratio": round(1 - (compressed_size / max(1, total_size)), 2),
                "files_preview": files[:10]
            }
            result.extracted_text = f"ZIP-Archiv: {len(files)} Dateien"
            result.summary = f"ZIP: {len(files)} Dateien, {total_size / 1024 / 1024:.1f} MB"
            result.completeness = 1.0
            result.confidence = 1.0
            
    except zipfile.BadZipFile:
        result.error = "Ungültiges ZIP-Format"
    except Exception as e:
        result.error = f"ZIP-Fehler: {str(e)[:100]}"
    
    return result


def _process_tar(filepath: Path, result: ExtendedProcessingResult) -> ExtendedProcessingResult:
    """TAR-Archiv mit Python tarfile (kein Entpacken)."""
    import tarfile
    
    def sanitize_filename(name: str) -> str:
        """Entferne ungültige Unicode-Zeichen (Surrogates)."""
        try:
            # Encode und decode mit 'surrogateescape' um Probleme zu vermeiden
            return name.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        except:
            return name[:50] + "..."
    
    try:
        # Bestimme Kompressionstyp
        mode = "r:*"  # Auto-detect compression
        
        with tarfile.open(filepath, mode) as tf:
            members = tf.getmembers()
            # Sanitize filenames to avoid UnicodeEncodeError
            files = [sanitize_filename(m.name) for m in members if m.isfile()]
            total_size = sum(m.size for m in members)
            
            result.success = True
            result.metadata = {
                "file_count": len(files),
                "total_size_bytes": total_size,
                "member_count": len(members),
                "files_preview": files[:10]
            }
            result.extracted_text = f"TAR-Archiv: {len(files)} Dateien"
            result.summary = f"TAR: {len(files)} Dateien, {total_size / 1024 / 1024:.1f} MB"
            result.completeness = 1.0
            result.confidence = 1.0
            
    except tarfile.TarError as e:
        result.error = f"TAR-Fehler: {str(e)[:100]}"
    except Exception as e:
        result.error = f"Fehler: {str(e)[:100]}"
    
    return result


def _process_gzip(filepath: Path, result: ExtendedProcessingResult) -> ExtendedProcessingResult:
    """GZIP-Datei Metadaten (kein Entpacken)."""
    import gzip
    
    try:
        # Nur Header lesen, nicht dekomprimieren
        with gzip.open(filepath, 'rb') as f:
            # Lese nur erste Bytes für Validierung
            f.read(100)
        
        compressed_size = filepath.stat().st_size
        
        result.success = True
        result.metadata = {
            "compressed_size_bytes": compressed_size,
            "type": "gzip"
        }
        result.extracted_text = f"GZIP: {compressed_size / 1024:.1f} KB komprimiert"
        result.summary = f"GZIP: {compressed_size / 1024:.1f} KB"
        result.completeness = 0.7  # Weniger Info als vollständige Archive
        result.confidence = 1.0
        
    except Exception as e:
        result.error = f"GZIP-Fehler: {str(e)[:100]}"
    
    return result


def _process_with_7zip(filepath: Path, result: ExtendedProcessingResult) -> ExtendedProcessingResult:
    """RAR/7z mit py7zr/rarfile (kein Docker-in-Docker nötig)."""
    ext = filepath.suffix.lower()
    
    try:
        if ext == ".7z":
            result = _process_7z_native(filepath, result)
        elif ext == ".rar":
            result = _process_rar_native(filepath, result)
        else:
            result.error = f"Unbekanntes Archiv-Format: {ext}"
    except Exception as e:
        result.error = f"Archiv-Fehler: {str(e)[:100]}"
    
    return result


def _process_7z_native(filepath: Path, result: ExtendedProcessingResult) -> ExtendedProcessingResult:
    """7z-Archiv mit py7zr (kein Entpacken)."""
    try:
        import py7zr
        
        with py7zr.SevenZipFile(filepath, mode='r') as archive:
            names = archive.getnames()
            
            # Dateigrößen aus Archiv-Info
            total_size = 0
            for info in archive.list():
                if hasattr(info, 'uncompressed'):
                    total_size += info.uncompressed
            
            result.success = True
            result.metadata = {
                "file_count": len(names),
                "total_size_bytes": total_size,
                "format": "7Z",
                "files_preview": names[:10]
            }
            result.extracted_text = f"7Z-Archiv: {len(names)} Dateien"
            result.summary = f"7Z: {len(names)} Dateien, {total_size / 1024 / 1024:.1f} MB"
            result.completeness = 0.95
            result.confidence = 1.0
            
    except ImportError:
        result.error = "py7zr nicht installiert"
    except Exception as e:
        result.error = f"7Z-Fehler: {str(e)[:100]}"
    
    return result


def _process_rar_native(filepath: Path, result: ExtendedProcessingResult) -> ExtendedProcessingResult:
    """RAR-Archiv mit rarfile (kein Entpacken)."""
    try:
        import rarfile
        
        with rarfile.RarFile(filepath) as archive:
            infos = archive.infolist()
            files = [f.filename for f in infos if not f.is_dir()]
            total_size = sum(f.file_size for f in infos)
            
            result.success = True
            result.metadata = {
                "file_count": len(files),
                "total_size_bytes": total_size,
                "format": "RAR",
                "is_solid": archive.is_solid() if hasattr(archive, 'is_solid') else None,
                "files_preview": files[:10]
            }
            result.extracted_text = f"RAR-Archiv: {len(files)} Dateien"
            result.summary = f"RAR: {len(files)} Dateien, {total_size / 1024 / 1024:.1f} MB"
            result.completeness = 0.95
            result.confidence = 1.0
            
    except ImportError:
        result.error = "rarfile nicht installiert"
    except rarfile.NeedFirstVolume:
        result.error = "Multi-Volume RAR: Erstes Volume benötigt"
    except rarfile.BadRarFile:
        result.error = "Ungültiges RAR-Format"
    except Exception as e:
        result.error = f"RAR-Fehler: {str(e)[:100]}"
    
    return result


# =============================================================================
# MAIN DISPATCHER
# =============================================================================

EXTENDED_PROCESSORS = {
    ".torrent": process_torrent,
    ".eml": process_eml,
    ".exr": process_exr,
    ".srt": process_srt,
    ".apk": process_apk,
    ".msg": process_msg,
    # 3D-Modelle (alle via trimesh)
    ".fbx": process_fbx,
    ".obj": process_fbx,
    ".stl": process_fbx,
    ".ply": process_fbx,
    ".gltf": process_fbx,
    ".glb": process_fbx,
    ".dae": process_fbx,
    ".3ds": process_fbx,
    # Archive (ohne Entpacken!)
    ".rar": process_archive,
    ".7z": process_archive,
    ".tar": process_archive,
    ".gz": process_archive,
    ".tgz": process_archive,
    ".zip": process_archive,
}


def process_extended_file(filepath: Path) -> ExtendedProcessingResult:
    """
    Verarbeite Datei mit erweitertem Processor.
    
    Returns:
        ExtendedProcessingResult oder None wenn Extension nicht unterstützt
    """
    ext = filepath.suffix.lower()
    
    if ext in EXTENDED_PROCESSORS:
        return EXTENDED_PROCESSORS[ext](filepath)
    
    return ExtendedProcessingResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=ext,
        file_type="unknown",
        error=f"Keine Erweiterung für {ext}"
    )


def is_extended_processable(filepath: Path) -> bool:
    """Prüfe ob Datei von diesem Modul verarbeitet werden kann."""
    return filepath.suffix.lower() in EXTENDED_PROCESSORS


def get_supported_extensions() -> List[str]:
    """Liste der unterstützten Erweiterungen."""
    return list(EXTENDED_PROCESSORS.keys())


# =============================================================================
# CLI / TEST
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("NEURAL VAULT - EXTENDED FILE PROCESSOR")
    print("=" * 60)
    print(f"\nUnterstützte Erweiterungen: {', '.join(get_supported_extensions())}")
    
    # Teste verfügbare Bibliotheken
    print("\nBibliotheken-Status:")
    
    libs = {
        "bencode2": ".torrent",
        "eml_parser": ".eml",
        "OpenEXR": ".exr",
        "extract_msg": ".msg"
    }
    
    for lib, ext in libs.items():
        try:
            __import__(lib)
            print(f"  ✅ {lib} ({ext})")
        except ImportError:
            print(f"  ❌ {lib} ({ext})")
    
    print("  ✅ regex (.srt) - built-in")
    print("  ✅ zipfile (.apk) - built-in")
    
    # Test mit Argument
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        if test_file.exists():
            print(f"\nTeste: {test_file}")
            result = process_extended_file(test_file)
            print(json.dumps(asdict(result), indent=2, default=str))
