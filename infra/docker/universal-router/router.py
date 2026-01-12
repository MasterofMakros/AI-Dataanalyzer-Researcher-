"""
Neural Vault Universal File Router
===================================

Erkennt JEDEN Dateityp und routet zum korrekten Processor.

Features:
- Magic Byte Detection (Datei-Signatur)
- MIME-Type Erkennung
- Extension-basiertes Fallback
- Dual-Path Routing (Fast/Deep)
- 200+ unterstützte Formate
"""

import os
import json
import asyncio
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
import logging
import struct

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")


# =============================================================================
# MAGIC BYTES DATABASE
# =============================================================================

MAGIC_SIGNATURES = {
    # Documents
    b"%PDF": ("pdf", "application/pdf"),
    b"PK\x03\x04": ("zip_based", None),  # ZIP, DOCX, XLSX, ODT, etc.
    b"\xd0\xcf\x11\xe0": ("ole2", None),  # DOC, XLS, PPT, MSG
    b"{\\rtf": ("rtf", "application/rtf"),

    # Images
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
    b"GIF87a": ("gif", "image/gif"),
    b"GIF89a": ("gif", "image/gif"),
    b"BM": ("bmp", "image/bmp"),
    b"II*\x00": ("tiff", "image/tiff"),
    b"MM\x00*": ("tiff", "image/tiff"),
    b"RIFF": ("riff", None),  # WAV, AVI, WebP
    b"8BPS": ("psd", "image/vnd.adobe.photoshop"),
    b"gimp xcf": ("xcf", "image/x-xcf"),
    b"AT&TFORM": ("djvu", "image/vnd.djvu"),

    # Audio
    b"\xff\xfb": ("mp3", "audio/mpeg"),
    b"\xff\xfa": ("mp3", "audio/mpeg"),
    b"ID3": ("mp3", "audio/mpeg"),
    b"fLaC": ("flac", "audio/flac"),
    b"OggS": ("ogg", "audio/ogg"),
    b"FORM": ("aiff", "audio/aiff"),
    b"MThd": ("mid", "audio/midi"),
    b"MAC ": ("ape", "audio/x-ape"),

    # Video
    b"\x1a\x45\xdf\xa3": ("mkv", "video/x-matroska"),  # MKV, WebM
    b"FLV\x01": ("flv", "video/x-flv"),
    b"\x00\x00\x01\xba": ("mpg", "video/mpeg"),
    b"\x00\x00\x01\xb3": ("mpg", "video/mpeg"),
    b"0&\xb2u": ("asf", None),  # WMV, WMA

    # Archives
    b"Rar!\x1a\x07": ("rar", "application/x-rar-compressed"),
    b"7z\xbc\xaf'": ("7z", "application/x-7z-compressed"),
    b"\x1f\x8b": ("gz", "application/gzip"),
    b"BZh": ("bz2", "application/x-bzip2"),
    b"\xfd7zXZ": ("xz", "application/x-xz"),
    b"(\xb5/\xfd": ("zst", "application/zstd"),

    # Executables
    b"MZ": ("exe", "application/x-msdownload"),
    b"\x7fELF": ("elf", "application/x-executable"),
    b"\xca\xfe\xba\xbe": ("macho", "application/x-mach-binary"),
    b"\xcf\xfa\xed\xfe": ("macho64", "application/x-mach-binary"),

    # Databases
    b"SQLite format 3": ("sqlite", "application/x-sqlite3"),

    # Special
    b"!BDN": ("pst", "application/vnd.ms-outlook-pst"),
    b"BOOKMOBI": ("mobi", "application/x-mobipocket-ebook"),
}


# ZIP-basierte Formate (nach PK\x03\x04)
ZIP_BASED_FORMATS = {
    "word/document.xml": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    "xl/workbook.xml": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "ppt/presentation.xml": ("pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    "content.xml": ("odt", "application/vnd.oasis.opendocument.text"),  # ODF
    "META-INF/container.xml": ("epub", "application/epub+zip"),
    "AndroidManifest.xml": ("apk", "application/vnd.android.package-archive"),
    "Payload/": ("ipa", "application/x-ios-app"),
    "mimetype": ("odf", None),  # Generic ODF
}


# OLE2-basierte Formate
OLE2_FORMATS = {
    "WordDocument": ("doc", "application/msword"),
    "Workbook": ("xls", "application/vnd.ms-excel"),
    "PowerPoint Document": ("ppt", "application/vnd.ms-powerpoint"),
    "__substg1.0_": ("msg", "application/vnd.ms-outlook"),
}


# =============================================================================
# QUEUE MAPPINGS
# =============================================================================

PROCESSOR_QUEUES = {
    # Documents → extract:documents (matches DocumentWorker.input_queue)
    "pdf": "extract:documents",
    "docx": "extract:documents",
    "xlsx": "extract:documents",
    "pptx": "extract:documents",
    "doc": "extract:documents",
    "xls": "extract:documents",
    "ppt": "extract:documents",
    "odt": "extract:documents",
    "ods": "extract:documents",
    "odp": "extract:documents",
    "rtf": "extract:documents",
    "txt": "extract:documents",
    "html": "extract:documents",
    "xml": "extract:documents",
    "json": "extract:documents",
    "md": "extract:documents",

    # Code Files - Programming Languages
    "py": "extract:documents",
    "js": "extract:documents",
    "ts": "extract:documents",
    "tsx": "extract:documents",
    "jsx": "extract:documents",
    "sh": "extract:documents",
    "ps1": "extract:documents",
    "sql": "extract:documents",
    "css": "extract:documents",
    "lua": "extract:documents",
    "c": "extract:documents",
    "cpp": "extract:documents",
    "cc": "extract:documents",
    "cxx": "extract:documents",
    "h": "extract:documents",
    "hpp": "extract:documents",
    "java": "extract:documents",
    "go": "extract:documents",
    "rs": "extract:documents",
    "rb": "extract:documents",
    "php": "extract:documents",
    "swift": "extract:documents",
    "kt": "extract:documents",
    "scala": "extract:documents",
    "r": "extract:documents",
    "pl": "extract:documents",
    "pm": "extract:documents",
    "asm": "extract:documents",
    "bas": "extract:documents",
    "vb": "extract:documents",
    "cs": "extract:documents",
    "fs": "extract:documents",
    "hs": "extract:documents",
    "elm": "extract:documents",
    "clj": "extract:documents",
    "ex": "extract:documents",
    "exs": "extract:documents",
    "erl": "extract:documents",
    "dart": "extract:documents",
    "vue": "extract:documents",
    "svelte": "extract:documents",
    "scss": "extract:documents",
    "sass": "extract:documents",
    "less": "extract:documents",
    "styl": "extract:documents",
    "coffee": "extract:documents",
    "bat": "extract:documents",
    "cmd": "extract:documents",
    "awk": "extract:documents",
    "sed": "extract:documents",
    "makefile": "extract:documents",
    "cmake": "extract:documents",
    "gradle": "extract:documents",
    "groovy": "extract:documents",
    
    # Config Files
    "yaml": "extract:documents",
    "yml": "extract:documents",
    "ini": "extract:documents",
    "toml": "extract:documents",
    "conf": "extract:documents",
    
    # Subtitles
    "srt": "extract:documents",
    "vtt": "extract:documents",
    "sub": "extract:documents",

    # E-Books
    "epub": "extract:ebooks",
    "mobi": "extract:ebooks",
    "azw": "extract:ebooks",
    "azw3": "extract:ebooks",
    "djvu": "extract:ebooks",

    # Images → extract:images (matches ImageWorker.input_queue)
    "jpg": "extract:images",
    "jpeg": "extract:images",
    "png": "extract:images",
    "gif": "extract:images",
    "bmp": "extract:images",
    "tiff": "extract:images",
    "tif": "extract:images",
    "webp": "extract:images",
    "heic": "extract:images",
    "psd": "extract:images",
    "raw": "extract:images",
    "cr2": "extract:images",
    "nef": "extract:images",
    "dng": "extract:images",
    "arw": "extract:images",
    "svg": "extract:images",
    "ico": "extract:images",
    "cur": "extract:images",
    "pcx": "extract:images",
    "tga": "extract:images",
    "exr": "extract:images",
    "hdr": "extract:images",

    # Audio → extract:audio (matches AudioWorker.input_queue)
    "mp3": "extract:audio",
    "wav": "extract:audio",
    "flac": "extract:audio",
    "m4a": "extract:audio",
    "aac": "extract:audio",
    "ogg": "extract:audio",
    "wma": "extract:audio",
    "mid": "extract:audio",
    "midi": "extract:audio",
    "ape": "extract:audio",
    "opus": "extract:audio",
    "amr": "extract:audio",
    "au": "extract:audio",
    "aiff": "extract:audio",
    "aif": "extract:audio",

    # Video → extract:video (matches VideoWorker.input_queue)
    "mp4": "extract:video",
    "mkv": "extract:video",
    "avi": "extract:video",
    "mov": "extract:video",
    "wmv": "extract:video",
    "webm": "extract:video",
    "flv": "extract:video",
    "mpg": "extract:video",
    "mpeg": "extract:video",
    "m4v": "extract:video",
    "3gp": "extract:video",
    "rm": "extract:video",
    "rmvb": "extract:video",
    "vob": "extract:video",
    "mts": "extract:video",
    "m2ts": "extract:video",
    # "ts": "extract:video",  # Conflict with TypeScript - default to Documents

    # Email → extract:email (matches EmailWorker.input_queue)
    "eml": "extract:email",
    "msg": "extract:email",

    # Archives → extract:archive (matches ArchiveWorker.input_queue)
    "zip": "extract:archive",
    "rar": "extract:archive",
    "7z": "extract:archive",
    "tar": "extract:archive",
    "gz": "extract:archive",
    "bz2": "extract:archive",
    "xz": "extract:archive",
    "lz": "extract:archive",
    "lzma": "extract:archive",
    "cab": "extract:archive",
    "iso": "extract:archive",
    "dmg": "extract:archive",

    # Databases → extract:databases
    "mdb": "extract:databases",
    "accdb": "extract:databases",
    "dbf": "extract:databases",
    "sqlite": "extract:databases",
    "sqlite3": "extract:databases",
    "db": "extract:databases",
    "db3": "extract:databases",
    
    # 3D Models
    "obj": "extract:3d",
    "stl": "extract:3d",
    "ply": "extract:3d",
    "glb": "extract:3d",
    "gltf": "extract:3d",
    "fbx": "extract:3d",

    # CAD
    "step": "extract:cad",
    "stp": "extract:cad",
    "iges": "extract:cad",
    "igs": "extract:cad",
    "dxf": "extract:cad",
    "dwg": "extract:cad",

    # GIS
    "geojson": "extract:gis",
    "shp": "extract:gis",
    "kml": "extract:gis",
    "gpx": "extract:gis",
    "gpkg": "extract:gis",

    # Fonts
    "woff": "extract:fonts",
    "woff2": "extract:fonts",
    "ttf": "extract:fonts",
    "otf": "extract:fonts",
    "eot": "extract:fonts",

    # Torrents
    "torrent": "extract:torrent",

    # Apps
    "apk": "extract:app",
    "ipa": "extract:app",
    "xapk": "extract:app",
    "apkm": "extract:app",

    # Executables (metadata only)
    "exe": "extract:binary:metadata",
    "dll": "extract:binary:metadata",
    "sys": "extract:binary:metadata",
    "elf": "extract:binary:metadata",
    "bin": "extract:binary:metadata",

    # Documentation/Latex
    "rst": "extract:documents",
    "cls": "extract:documents",
    "log": "extract:documents",
    "diff": "extract:documents",
    "patch": "extract:documents",

    # Scientific Formats → extract:scientific
    "csv": "extract:scientific",
    "tsv": "extract:scientific",
    "jsonl": "extract:scientific",
    "tex": "extract:scientific",
    "bib": "extract:scientific",
    "ris": "extract:scientific",
    "rmd": "extract:scientific",
    "ipynb": "extract:scientific",
    "mat": "extract:scientific",
    "h5": "extract:scientific",
    "hdf5": "extract:scientific",
    "nc": "extract:scientific",

    # Encrypted (skip)
    "gpg": "skip",
    "pgp": "skip",

    # Fallback
    "*": "extract:unknown",
}


# =============================================================================
# FILE TYPE DETECTOR
# =============================================================================

class FileTypeDetector:
    """Erkennt Dateitypen über Magic Bytes und Extension."""

    def __init__(self):
        mimetypes.init()

    async def detect(self, filepath: str) -> Tuple[str, str, str]:
        """
        Erkennt Dateityp.

        Returns:
            (extension, mime_type, detection_method)
        """
        path = Path(filepath)
        ext_from_name = path.suffix.lower().lstrip(".")

        # 1. Magic Bytes prüfen
        magic_result = await self._detect_magic(filepath)
        if magic_result:
            detected_ext, mime_type = magic_result
            if detected_ext and detected_ext != "zip_based" and detected_ext != "ole2":
                return (detected_ext, mime_type or mimetypes.guess_type(f"file.{detected_ext}")[0], "magic")

            # ZIP-basierte Formate genauer prüfen
            if detected_ext == "zip_based":
                zip_result = await self._detect_zip_contents(filepath)
                if zip_result:
                    return (*zip_result, "zip_content")

            # OLE2-basierte Formate genauer prüfen
            if detected_ext == "ole2":
                ole_result = await self._detect_ole_contents(filepath)
                if ole_result:
                    return (*ole_result, "ole_content")

        # 2. RIFF-Container prüfen (WAV, AVI, WebP)
        if magic_result and magic_result[0] == "riff":
            riff_result = await self._detect_riff_subtype(filepath)
            if riff_result:
                return (*riff_result, "riff_subtype")

        # 3. MP4/MOV Container prüfen
        ftyp_result = await self._detect_ftyp(filepath)
        if ftyp_result:
            return (*ftyp_result, "ftyp")

        # 4. Extension-basierter Fallback
        if ext_from_name:
            mime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
            return (ext_from_name, mime, "extension")

        # 5. Unbekannt
        return ("unknown", "application/octet-stream", "unknown")

    async def _detect_magic(self, filepath: str) -> Optional[Tuple[str, str]]:
        """Prüft Magic Bytes."""
        try:
            with open(filepath, "rb") as f:
                header = f.read(32)

            for magic, (ext, mime) in MAGIC_SIGNATURES.items():
                if header.startswith(magic):
                    return (ext, mime)

        except Exception as e:
            logger.error(f"Magic detection error: {e}")

        return None

    async def _detect_zip_contents(self, filepath: str) -> Optional[Tuple[str, str]]:
        """Prüft ZIP-Inhalte für Office/EPUB/APK."""
        import zipfile

        try:
            with zipfile.ZipFile(filepath, "r") as zf:
                names = zf.namelist()

                for content_path, (ext, mime) in ZIP_BASED_FORMATS.items():
                    for name in names:
                        if content_path in name:
                            return (ext, mime)

                # Generisches ZIP
                return ("zip", "application/zip")

        except zipfile.BadZipFile:
            return None
        except Exception as e:
            logger.error(f"ZIP detection error: {e}")
            return None

    async def _detect_ole_contents(self, filepath: str) -> Optional[Tuple[str, str]]:
        """Prüft OLE2-Streams für Office/MSG."""
        try:
            # Vereinfachte Erkennung basierend auf Dateigröße und Header
            with open(filepath, "rb") as f:
                data = f.read(4096)

            # Nach typischen Strings suchen
            if b"W\x00o\x00r\x00d" in data:
                return ("doc", "application/msword")
            if b"W\x00o\x00r\x00k\x00b\x00o\x00o\x00k" in data:
                return ("xls", "application/vnd.ms-excel")
            if b"P\x00o\x00w\x00e\x00r\x00P\x00o\x00i\x00n\x00t" in data:
                return ("ppt", "application/vnd.ms-powerpoint")
            if b"__substg1" in data:
                return ("msg", "application/vnd.ms-outlook")

            return ("ole2", "application/x-ole-storage")

        except Exception as e:
            logger.error(f"OLE detection error: {e}")
            return None

    async def _detect_riff_subtype(self, filepath: str) -> Optional[Tuple[str, str]]:
        """Erkennt RIFF-Subtypen (WAV, AVI, WebP)."""
        try:
            with open(filepath, "rb") as f:
                f.seek(8)
                fourcc = f.read(4)

            if fourcc == b"WAVE":
                return ("wav", "audio/wav")
            if fourcc == b"AVI ":
                return ("avi", "video/x-msvideo")
            if fourcc == b"WEBP":
                return ("webp", "image/webp")

        except Exception as e:
            logger.error(f"RIFF detection error: {e}")

        return None

    async def _detect_ftyp(self, filepath: str) -> Optional[Tuple[str, str]]:
        """Erkennt MP4/MOV/3GP über ftyp Box."""
        try:
            with open(filepath, "rb") as f:
                # Suche nach ftyp in den ersten 32 Bytes
                data = f.read(32)

            if b"ftyp" not in data:
                return None

            ftyp_pos = data.find(b"ftyp")
            brand = data[ftyp_pos + 4:ftyp_pos + 8]

            brand_mapping = {
                b"isom": ("mp4", "video/mp4"),
                b"mp41": ("mp4", "video/mp4"),
                b"mp42": ("mp4", "video/mp4"),
                b"M4V ": ("m4v", "video/x-m4v"),
                b"M4A ": ("m4a", "audio/mp4"),
                b"M4B ": ("m4b", "audio/mp4"),
                b"qt  ": ("mov", "video/quicktime"),
                b"3gp4": ("3gp", "video/3gpp"),
                b"3gp5": ("3gp", "video/3gpp"),
                b"3g2a": ("3g2", "video/3gpp2"),
            }

            for brand_code, result in brand_mapping.items():
                if brand.startswith(brand_code[:4]):
                    return result

            # Generisches MP4
            return ("mp4", "video/mp4")

        except Exception as e:
            logger.error(f"ftyp detection error: {e}")

        return None


# =============================================================================
# ROUTER
# =============================================================================

@dataclass
class RoutingDecision:
    """Routing-Entscheidung für eine Datei."""
    filepath: str
    filename: str
    extension: str
    mime_type: str
    detection_method: str
    target_queue: str
    priority: int
    processing_path: str
    metadata: Dict[str, Any]


class UniversalRouter:
    """Routet Dateien zu korrekten Processor-Queues."""

    def __init__(self):
        self.detector = FileTypeDetector()
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        self.redis = await redis.from_url(
            REDIS_URL,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True
        )

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def route(self, filepath: str, force_deep: bool = False) -> RoutingDecision:
        """
        Analysiert Datei und bestimmt Routing.
        """
        path = Path(filepath)
        filename = path.name
        file_size = path.stat().st_size if path.exists() else 0
        modified = datetime.fromtimestamp(path.stat().st_mtime) if path.exists() else datetime.now()

        # 1. Dateityp erkennen
        extension, mime_type, detection_method = await self.detector.detect(filepath)

        # 2. Queue bestimmen
        target_queue = PROCESSOR_QUEUES.get(extension, PROCESSOR_QUEUES.get("*"))

        # 3. Priority berechnen
        priority = self._calculate_priority(extension, filename, file_size, modified)

        # 4. Processing Path bestimmen
        processing_path = self._determine_path(extension, file_size, priority, force_deep)

        return RoutingDecision(
            filepath=filepath,
            filename=filename,
            extension=extension,
            mime_type=mime_type,
            detection_method=detection_method,
            target_queue=target_queue,
            priority=priority,
            processing_path=processing_path,
            metadata={
                "size": file_size,
                "modified": modified.isoformat(),
            }
        )

    def _calculate_priority(self, ext: str, filename: str, size: int, modified: datetime) -> int:
        """Berechnet Priority Score."""
        score = 50

        # Recency Boost
        age = datetime.now() - modified
        if age.total_seconds() < 3600:
            score += 30
        elif age.total_seconds() < 86400:
            score += 20
        elif age.total_seconds() < 604800:
            score += 10

        # Type Priority
        type_priority = {
            "eml": 25, "msg": 25, "pst": 25,  # Email
            "pdf": 15, "docx": 15, "xlsx": 12,  # Documents
            "mp3": 12, "wav": 12, "m4a": 12,  # Audio
            "mp4": 8, "mkv": 8,  # Video
            "jpg": 5, "png": 5,  # Images
        }
        score += type_priority.get(ext, 0)

        # Keyword Boost
        keywords = ["vertrag", "rechnung", "passwort", "steuer", "bank", "wichtig", "dringend"]
        if any(kw in filename.lower() for kw in keywords):
            score += 15

        # Size Penalty
        if size > 100 * 1024 * 1024 and score < 70:
            score -= 10

        return min(100, max(0, score))

    def _determine_path(self, ext: str, size: int, priority: int, force_deep: bool) -> str:
        """Bestimmt Fast vs Deep Path."""
        if force_deep:
            return "deep"

        # Große Dateien → Deep
        if size > 50 * 1024 * 1024:
            return "deep"

        # Hohe Priorität + Klein → Fast
        if priority >= 70 and size < 10 * 1024 * 1024:
            return "fast"

        # Komplexe Typen → Deep
        deep_types = ["pdf", "mp3", "wav", "m4a", "mp4", "mkv", "avi", "pst"]
        if ext in deep_types:
            return "deep"

        return "fast"

    async def enqueue(self, decision: RoutingDecision) -> str:
        """Fügt Job in Queue ein."""
        # Get file stats for Worker FileJob compatibility
        try:
            file_stat = Path(decision.filepath).stat()
            file_size = file_stat.st_size
            file_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        except Exception:
            file_size = 0
            file_modified = datetime.now().isoformat()
        
        job_data = {
            "id": f"{datetime.now().timestamp():.6f}",
            "path": decision.filepath,  # Worker expects 'path' not 'filepath'
            "filename": decision.filename,
            "extension": decision.extension,
            "size": file_size,  # Required by Worker FileJob
            "modified": file_modified,  # Required by Worker FileJob
            "mime_type": decision.mime_type,
            "priority": decision.priority,
            "processing_path": decision.processing_path,
            "metadata": decision.metadata,
            "created_at": datetime.now().isoformat()
        }

        message_id = await self.redis.xadd(
            decision.target_queue,
            {"data": json.dumps(job_data)},
            maxlen=50000
        )

        logger.info(f"Routed {decision.filename} → {decision.target_queue} (P{decision.priority})")

        return message_id


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Neural Vault Universal Router",
    description="Routes any file type to the correct processor",
    version="1.0.0"
)

router = UniversalRouter()


class RouteRequest(BaseModel):
    filepath: str
    force_deep: bool = False


class RouteResponse(BaseModel):
    filepath: str
    extension: str
    mime_type: str
    detection_method: str
    target_queue: str
    priority: int
    processing_path: str


class BatchRouteRequest(BaseModel):
    filepaths: List[str]
    force_deep: bool = False


@app.on_event("startup")
async def startup():
    await router.connect()
    
    # Create consumer group for intake streams
    intake_streams = ["intake:priority", "intake:normal", "intake:bulk"]
    consumer_group = "router-consumers"
    
    for stream in intake_streams:
        try:
            await router.redis.xgroup_create(stream, consumer_group, id="0", mkstream=True)
            logger.info(f"Created consumer group '{consumer_group}' for stream '{stream}'")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{consumer_group}' already exists for '{stream}'")
            else:
                logger.error(f"Error creating consumer group: {e}")
    
    # Start background consumer task
    app.state.consumer_task = asyncio.create_task(
        consume_intake_queues(router, intake_streams, consumer_group)
    )
    logger.info("Started intake consumer background task")


async def consume_intake_queues(router_instance, streams: list, group: str):
    """Background task that consumes from intake streams and routes to extraction queues."""
    import socket
    consumer_name = f"router-{socket.gethostname()}-{os.getpid()}"
    
    logger.info(f"Consumer '{consumer_name}' starting for streams: {streams}")
    
    while True:
        try:
            # Read from all intake streams
            messages = await router_instance.redis.xreadgroup(
                groupname=group,
                consumername=consumer_name,
                streams={s: ">" for s in streams},
                count=10,
                block=5000  # Block for 5 seconds
            )
            
            if not messages:
                continue
                
            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    try:
                        # Parse the job data
                        raw_data = message_data.get("data") or message_data.get("job")
                        if not raw_data:
                            logger.warning(f"Empty message data: {message_data}")
                            await router_instance.redis.xack(stream_name, group, message_id)
                            continue
                        
                        job = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                        filepath = job.get("path") or job.get("filepath")
                        
                        if not filepath:
                            logger.warning(f"No filepath in job: {job}")
                            await router_instance.redis.xack(stream_name, group, message_id)
                            continue
                        
                        # Route the file to the correct extraction queue
                        decision = await router_instance.route(filepath)
                        await router_instance.enqueue(decision)
                        
                        # Acknowledge the message
                        await router_instance.redis.xack(stream_name, group, message_id)
                        logger.info(f"Routed job from {stream_name}: {filepath} → {decision.target_queue}")
                        
                    except Exception as e:
                        logger.error(f"Error processing message {message_id}: {e}")
                        # Don't ack - message will be reprocessed
                        
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled, shutting down...")
            break
        except Exception as e:
            logger.error(f"Consumer loop error: {e}")
            await asyncio.sleep(1)  # Backoff on error


@app.on_event("shutdown")
async def shutdown():
    # Cancel consumer task
    if hasattr(app.state, 'consumer_task'):
        app.state.consumer_task.cancel()
        try:
            await app.state.consumer_task
        except asyncio.CancelledError:
            pass
        logger.info("Consumer task stopped")
    
    await router.disconnect()


@app.get("/health")
async def health():
    try:
        await router.redis.ping()
        return {"status": "healthy"}
    except Exception:
        return {"status": "unhealthy"}


@app.post("/detect")
async def detect_type(request: RouteRequest) -> RouteResponse:
    """Erkennt Dateityp ohne zu routen."""
    decision = await router.route(request.filepath, request.force_deep)
    return RouteResponse(
        filepath=decision.filepath,
        extension=decision.extension,
        mime_type=decision.mime_type,
        detection_method=decision.detection_method,
        target_queue=decision.target_queue,
        priority=decision.priority,
        processing_path=decision.processing_path
    )


@app.post("/route")
async def route_file(request: RouteRequest) -> Dict[str, Any]:
    """Erkennt Dateityp und fügt in Queue ein."""
    decision = await router.route(request.filepath, request.force_deep)
    message_id = await router.enqueue(decision)

    return {
        "message_id": message_id,
        "queue": decision.target_queue,
        "extension": decision.extension,
        "priority": decision.priority,
        "processing_path": decision.processing_path
    }


@app.post("/route/batch")
async def route_batch(request: BatchRouteRequest) -> Dict[str, Any]:
    """Routet mehrere Dateien."""
    results = []
    for filepath in request.filepaths:
        try:
            decision = await router.route(filepath, request.force_deep)
            message_id = await router.enqueue(decision)
            results.append({
                "filepath": filepath,
                "status": "queued",
                "queue": decision.target_queue,
                "message_id": message_id
            })
        except Exception as e:
            results.append({
                "filepath": filepath,
                "status": "error",
                "error": str(e)
            })

    return {
        "total": len(request.filepaths),
        "queued": len([r for r in results if r["status"] == "queued"]),
        "results": results
    }


@app.get("/queues")
async def list_queues():
    """Listet alle Queues mit Statistiken."""
    stats = {}
    for ext, queue in PROCESSOR_QUEUES.items():
        if queue not in stats:
            try:
                info = await router.redis.xinfo_stream(queue)
                stats[queue] = info.get("length", 0)
            except Exception:
                stats[queue] = 0
    return stats


@app.get("/formats")
async def list_formats():
    """Listet alle unterstützten Formate."""
    return {
        "total": len(PROCESSOR_QUEUES) - 1,
        "formats": list(PROCESSOR_QUEUES.keys())
    }


@app.get("/magic-signatures")
async def list_signatures():
    """Listet alle Magic Byte Signaturen."""
    return {
        sig.hex(): result
        for sig, result in MAGIC_SIGNATURES.items()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8030)
