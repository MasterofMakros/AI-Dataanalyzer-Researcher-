"""
Neural Vault Enhanced Extraction
================================

Drop-in Ersatz für die Extraktions-Funktionen in smart_ingest.py.
Fügt hinzu:
- Magic Byte Detection
- Format Registry Lookup
- Tika HTML→Markdown (Tabellenerhalt)
- Context Headers für RAG

Usage in smart_ingest.py:
    from scripts.utils.enhanced_extraction import (
        detect_file_type,
        extract_text_enhanced,
        get_all_supported_extensions,
        prepare_for_indexing
    )
"""

import re
import requests
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

# Optionale Imports
try:
    from markdownify import markdownify as md
    MARKDOWNIFY_AVAILABLE = True
except ImportError:
    MARKDOWNIFY_AVAILABLE = False

# Interne Imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from config.format_registry import FORMAT_REGISTRY, get_format_spec, ProcessorType
    FORMAT_REGISTRY_AVAILABLE = True
except ImportError:
    FORMAT_REGISTRY_AVAILABLE = False
    FORMAT_REGISTRY = {}

from config.paths import TIKA_URL


# =============================================================================
# MAGIC BYTE SIGNATURES
# =============================================================================

MAGIC_SIGNATURES = {
    # Documents
    b"%PDF": ("pdf", "application/pdf"),
    b"PK\x03\x04": ("zip_based", None),
    b"\xd0\xcf\x11\xe0": ("ole2", None),
    b"{\\rtf": ("rtf", "application/rtf"),

    # Images
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
    b"GIF87a": ("gif", "image/gif"),
    b"GIF89a": ("gif", "image/gif"),
    b"BM": ("bmp", "image/bmp"),
    b"II*\x00": ("tiff", "image/tiff"),
    b"MM\x00*": ("tiff", "image/tiff"),
    b"RIFF": ("riff", None),
    b"8BPS": ("psd", "image/vnd.adobe.photoshop"),

    # Audio
    b"\xff\xfb": ("mp3", "audio/mpeg"),
    b"\xff\xfa": ("mp3", "audio/mpeg"),
    b"ID3": ("mp3", "audio/mpeg"),
    b"fLaC": ("flac", "audio/flac"),
    b"OggS": ("ogg", "audio/ogg"),
    b"MThd": ("mid", "audio/midi"),

    # Video
    b"\x1a\x45\xdf\xa3": ("mkv", "video/x-matroska"),
    b"FLV\x01": ("flv", "video/x-flv"),
    b"\x00\x00\x01\xba": ("mpg", "video/mpeg"),

    # Archives
    b"Rar!\x1a\x07": ("rar", "application/x-rar-compressed"),
    b"7z\xbc\xaf'": ("7z", "application/x-7z-compressed"),
    b"\x1f\x8b": ("gz", "application/gzip"),
    b"BZh": ("bz2", "application/x-bzip2"),

    # Database
    b"SQLite format 3": ("sqlite", "application/x-sqlite3"),

    # Executables
    b"MZ": ("exe", "application/x-msdownload"),
    b"\x7fELF": ("elf", "application/x-executable"),

    # Email
    b"!BDN": ("pst", "application/vnd.ms-outlook-pst"),
}


# =============================================================================
# FILE TYPE DETECTION
# =============================================================================

@dataclass
class FileTypeInfo:
    """Informationen über einen erkannten Dateityp."""
    extension: str
    mime_type: str
    detection_method: str  # magic, container, extension
    category: str = "unknown"
    processor: str = "tika"


def detect_file_type(filepath: Path) -> FileTypeInfo:
    """
    Erkennt Dateityp über Magic Bytes mit Extension-Fallback.

    Args:
        filepath: Pfad zur Datei

    Returns:
        FileTypeInfo mit Extension, MIME-Type, Detection-Method
    """
    ext_from_name = filepath.suffix.lower().lstrip(".")
    default_mime = "application/octet-stream"

    # 1. Magic Bytes prüfen
    try:
        with open(filepath, "rb") as f:
            header = f.read(64)

        for magic, (ext, mime) in MAGIC_SIGNATURES.items():
            if header.startswith(magic):
                # ZIP-basierte Formate genauer analysieren
                if ext == "zip_based":
                    zip_result = _detect_zip_content(filepath)
                    if zip_result:
                        return FileTypeInfo(
                            extension=zip_result[0],
                            mime_type=zip_result[1],
                            detection_method="container",
                            category=_get_category(zip_result[0]),
                            processor=_get_processor(zip_result[0])
                        )
                    # Fallback zu ZIP
                    return FileTypeInfo(
                        extension="zip",
                        mime_type="application/zip",
                        detection_method="magic",
                        category="archive",
                        processor="archive"
                    )

                # OLE2-basierte Formate
                if ext == "ole2":
                    ole_result = _detect_ole_content(header)
                    if ole_result:
                        return FileTypeInfo(
                            extension=ole_result[0],
                            mime_type=ole_result[1],
                            detection_method="container",
                            category=_get_category(ole_result[0]),
                            processor=_get_processor(ole_result[0])
                        )

                # RIFF-Container (WAV, AVI, WebP)
                if ext == "riff":
                    riff_result = _detect_riff_subtype(header)
                    if riff_result:
                        return FileTypeInfo(
                            extension=riff_result[0],
                            mime_type=riff_result[1],
                            detection_method="container",
                            category=_get_category(riff_result[0]),
                            processor=_get_processor(riff_result[0])
                        )

                # Normales Magic-Match
                return FileTypeInfo(
                    extension=ext,
                    mime_type=mime or default_mime,
                    detection_method="magic",
                    category=_get_category(ext),
                    processor=_get_processor(ext)
                )

        # MP4/MOV ftyp Detection
        if b"ftyp" in header[:32]:
            ftyp_result = _detect_ftyp(header)
            if ftyp_result:
                return FileTypeInfo(
                    extension=ftyp_result[0],
                    mime_type=ftyp_result[1],
                    detection_method="container",
                    category="video",
                    processor="ffmpeg"
                )

    except Exception:
        pass

    # 2. Extension Fallback
    if ext_from_name:
        return FileTypeInfo(
            extension=ext_from_name,
            mime_type=_guess_mime(ext_from_name),
            detection_method="extension",
            category=_get_category(ext_from_name),
            processor=_get_processor(ext_from_name)
        )

    return FileTypeInfo(
        extension="unknown",
        mime_type=default_mime,
        detection_method="unknown",
        category="unknown",
        processor="binary"
    )


def _detect_zip_content(filepath: Path) -> Optional[Tuple[str, str]]:
    """Analysiert ZIP-Inhalt für Office/EPUB/APK."""
    import zipfile

    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            names = zf.namelist()

            patterns = {
                "word/document.xml": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                "xl/workbook.xml": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                "ppt/presentation.xml": ("pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
                "META-INF/container.xml": ("epub", "application/epub+zip"),
                "content.xml": ("odt", "application/vnd.oasis.opendocument.text"),
                "AndroidManifest.xml": ("apk", "application/vnd.android.package-archive"),
            }

            for name in names:
                for pattern, result in patterns.items():
                    if pattern in name:
                        return result

    except Exception:
        pass

    return None


def _detect_ole_content(header: bytes) -> Optional[Tuple[str, str]]:
    """Analysiert OLE2-Header für Office/MSG."""
    # Vereinfachte Erkennung
    if b"W\x00o\x00r\x00d" in header:
        return ("doc", "application/msword")
    if b"__substg1" in header:
        return ("msg", "application/vnd.ms-outlook")
    return None


def _detect_riff_subtype(header: bytes) -> Optional[Tuple[str, str]]:
    """Erkennt RIFF-Subtyp."""
    if len(header) >= 12:
        fourcc = header[8:12]
        if fourcc == b"WAVE":
            return ("wav", "audio/wav")
        if fourcc == b"AVI ":
            return ("avi", "video/x-msvideo")
        if fourcc == b"WEBP":
            return ("webp", "image/webp")
    return None


def _detect_ftyp(header: bytes) -> Optional[Tuple[str, str]]:
    """Erkennt MP4/MOV über ftyp."""
    ftyp_pos = header.find(b"ftyp")
    if ftyp_pos >= 0 and ftyp_pos + 8 <= len(header):
        brand = header[ftyp_pos + 4:ftyp_pos + 8]

        brands = {
            b"isom": ("mp4", "video/mp4"),
            b"mp41": ("mp4", "video/mp4"),
            b"mp42": ("mp4", "video/mp4"),
            b"M4V ": ("m4v", "video/x-m4v"),
            b"M4A ": ("m4a", "audio/mp4"),
            b"qt  ": ("mov", "video/quicktime"),
        }

        for b, result in brands.items():
            if brand.startswith(b[:4]):
                return result

        return ("mp4", "video/mp4")

    return None


def _get_category(ext: str) -> str:
    """Holt Kategorie aus Format Registry oder Fallback."""
    if FORMAT_REGISTRY_AVAILABLE and ext in FORMAT_REGISTRY:
        return FORMAT_REGISTRY[ext].category

    categories = {
        "pdf": "documents", "docx": "documents", "xlsx": "documents",
        "doc": "documents", "xls": "documents", "txt": "documents",
        "jpg": "images", "png": "images", "gif": "images",
        "mp3": "audio", "wav": "audio", "flac": "audio",
        "mp4": "video", "mkv": "video", "avi": "video",
        "eml": "email", "msg": "email",
        "zip": "archive", "rar": "archive", "7z": "archive",
    }
    return categories.get(ext, "unknown")


def _get_processor(ext: str) -> str:
    """Holt Processor aus Format Registry oder Fallback."""
    if FORMAT_REGISTRY_AVAILABLE and ext in FORMAT_REGISTRY:
        return FORMAT_REGISTRY[ext].processor.value

    processors = {
        "pdf": "tika", "docx": "tika", "xlsx": "tika",
        "jpg": "ocr", "png": "ocr",
        "mp3": "whisper", "wav": "whisper",
        "mp4": "ffmpeg", "mkv": "ffmpeg",
        "eml": "email", "msg": "email",
        "zip": "archive", "rar": "archive",
    }
    return processors.get(ext, "tika")


def _guess_mime(ext: str) -> str:
    """Rät MIME-Type aus Extension."""
    mimes = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "doc": "application/msword",
        "xls": "application/vnd.ms-excel",
        "txt": "text/plain",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "mp4": "video/mp4",
        "mkv": "video/x-matroska",
    }
    return mimes.get(ext, "application/octet-stream")


# =============================================================================
# ENHANCED TEXT EXTRACTION
# =============================================================================

def extract_text_enhanced(
    filepath: Path,
    prefer_markdown: bool = True,
    tika_url: str = None
) -> Tuple[str, str]:
    """
    Extrahiert Text mit HTML→Markdown Konvertierung.

    Args:
        filepath: Pfad zur Datei
        prefer_markdown: HTML holen und zu Markdown konvertieren
        tika_url: Optionale Tika-URL

    Returns:
        (text, format) - Extrahierter Text und Format ("markdown" oder "plain")
    """
    url = tika_url or TIKA_URL

    if prefer_markdown:
        # HTML holen
        try:
            with open(filepath, "rb") as f:
                response = requests.put(
                    url,
                    data=f,
                    headers={"Accept": "text/html"},
                    timeout=120
                )
            if response.status_code == 200 and response.text.strip():
                markdown = _html_to_markdown(response.text)
                return markdown, "markdown"
        except Exception:
            pass

    # Fallback: Plain Text
    try:
        with open(filepath, "rb") as f:
            response = requests.put(
                url,
                data=f,
                headers={"Accept": "text/plain"},
                timeout=120
            )
        if response.status_code == 200:
            return response.text.strip(), "plain"
    except Exception:
        pass

    return "", "error"


def _html_to_markdown(html: str) -> str:
    """Konvertiert HTML zu Markdown."""
    if MARKDOWNIFY_AVAILABLE:
        try:
            markdown = md(
                html,
                heading_style="ATX",
                bullets="-",
                strip=["script", "style"],
                convert=["table", "tr", "td", "th", "p", "h1", "h2", "h3", "h4", "ul", "ol", "li", "a", "strong", "em"]
            )
            return _cleanup_markdown(markdown)
        except Exception:
            pass

    # Fallback ohne markdownify
    import html as html_module

    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<tr[^>]*>', '| ', text, flags=re.IGNORECASE)
    text = re.sub(r'</tr>', ' |\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<t[dh][^>]*>(.*?)</t[dh]>', r'\1 | ', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_module.unescape(text)

    return _cleanup_markdown(text)


def _cleanup_markdown(text: str) -> str:
    """Bereinigt Markdown."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


# =============================================================================
# CONTEXT HEADERS
# =============================================================================

def add_context_header(
    text: str,
    filename: str,
    file_type: FileTypeInfo,
    category: Optional[str] = None,
    confidence: Optional[float] = None,
    page: Optional[int] = None,
    timestamp_start: Optional[float] = None,
    timestamp_end: Optional[float] = None
) -> str:
    """
    Fügt Context Header für RAG hinzu.

    Args:
        text: Der zu wrappende Text
        filename: Dateiname
        file_type: FileTypeInfo vom Detection
        category: Klassifikations-Kategorie
        confidence: Klassifikations-Konfidenz
        page: Seitenzahl (für PDFs)
        timestamp_start: Start-Zeit (für Audio/Video)
        timestamp_end: End-Zeit (für Audio/Video)

    Returns:
        Text mit Context Header
    """
    header_parts = [
        f"SOURCE: {filename}",
        f"TYPE: {file_type.extension}",
    ]

    if page is not None:
        header_parts.append(f"PAGE: {page}")

    if timestamp_start is not None:
        ts = _format_timestamp(timestamp_start)
        if timestamp_end is not None:
            ts += f"-{_format_timestamp(timestamp_end)}"
        header_parts.append(f"TIME: {ts}")

    header_line_1 = f"[{' | '.join(header_parts)}]"

    meta_parts = []
    if category:
        meta_parts.append(f"CATEGORY: {category}")
    if confidence is not None:
        meta_parts.append(f"CONFIDENCE: {confidence:.2f}")

    if meta_parts:
        header_line_2 = f"[{' | '.join(meta_parts)}]"
        return f"{header_line_1}\n{header_line_2}\n---\n{text}"

    return f"{header_line_1}\n---\n{text}"


def _format_timestamp(seconds: float) -> str:
    """Formatiert Sekunden als MM:SS oder HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


# =============================================================================
# PREPARE FOR INDEXING
# =============================================================================

def prepare_for_indexing(
    doc: Dict[str, Any],
    add_headers: bool = True
) -> Dict[str, Any]:
    """
    Bereitet ein Dokument für die Indexierung vor.

    Fügt hinzu:
    - Zeitstempel-Felder (year_created, month_created, etc.)
    - Context Headers (optional)
    - Entities flatten

    Args:
        doc: Das Dokument-Dict
        add_headers: Context Headers hinzufügen

    Returns:
        Aufbereitetes Dokument
    """
    from datetime import datetime

    result = doc.copy()

    # Zeitstempel-Felder für Pattern-of-Life
    for field, ts_field in [
        ("file_created", "file_created_timestamp"),
        ("file_modified", "file_modified_timestamp"),
        ("indexed_at", "indexed_at_timestamp")
    ]:
        if field in doc and doc[field]:
            try:
                if isinstance(doc[field], str):
                    dt = datetime.fromisoformat(doc[field].replace("Z", "+00:00"))
                else:
                    dt = doc[field]

                result[ts_field] = int(dt.timestamp())

                if field == "file_created":
                    result["year_created"] = dt.year
                    result["month_created"] = dt.month
                    result["weekday_created"] = dt.weekday()
                    result["hour_created"] = dt.hour
            except Exception:
                pass

    # Entities flatten für Suche
    if "entities" in doc and isinstance(doc["entities"], dict):
        flat_parts = []
        for key, value in doc["entities"].items():
            if isinstance(value, list):
                flat_parts.extend([str(v) for v in value])
            elif value:
                flat_parts.append(str(value))
        result["entities_flat"] = " ".join(flat_parts)

    # Source Type aus Extension
    if "extension" in doc:
        ext = doc["extension"].lower().lstrip(".")
        type_mapping = {
            "pdf": "pdf",
            "docx": "document", "doc": "document", "txt": "document",
            "xlsx": "spreadsheet", "xls": "spreadsheet", "csv": "spreadsheet",
            "jpg": "image", "jpeg": "image", "png": "image",
            "mp3": "audio", "wav": "audio", "m4a": "audio",
            "mp4": "video", "mkv": "video", "avi": "video",
            "eml": "email", "msg": "email"
        }
        result["source_type"] = type_mapping.get(ext, "other")

    # Context Headers
    if add_headers and result.get("extracted_text"):
        file_type = FileTypeInfo(
            extension=result.get("extension", "unknown"),
            mime_type=result.get("mime_type", "application/octet-stream"),
            detection_method="database",
            category=result.get("category", "unknown")
        )

        result["extracted_text"] = add_context_header(
            text=result["extracted_text"],
            filename=result.get("original_filename", "unknown"),
            file_type=file_type,
            category=result.get("category"),
            confidence=result.get("confidence")
        )

    return result


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_supported_extensions() -> set:
    """Gibt alle unterstützten Extensions zurück."""
    if FORMAT_REGISTRY_AVAILABLE:
        return {f".{ext}" for ext in FORMAT_REGISTRY.keys() if ext != "*"}

    # Fallback
    return {
        ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
        ".txt", ".rtf", ".md", ".csv", ".json", ".xml", ".html",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",
        ".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg",
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm",
        ".eml", ".msg",
        ".zip", ".rar", ".7z", ".tar", ".gz",
        ".py", ".js", ".ts", ".java", ".c", ".cpp",
    }


def is_supported(filepath: Path) -> bool:
    """Prüft ob Datei unterstützt wird."""
    return filepath.suffix.lower() in get_all_supported_extensions()


# =============================================================================
# MAIN (Test)
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python enhanced_extraction.py <filepath>")
        print("\nTest mit einer Datei:")
        print("  python enhanced_extraction.py /path/to/document.pdf")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"Datei nicht gefunden: {filepath}")
        sys.exit(1)

    print(f"Analysiere: {filepath}")
    print("-" * 50)

    # 1. Dateityp erkennen
    file_type = detect_file_type(filepath)
    print(f"Extension: {file_type.extension}")
    print(f"MIME-Type: {file_type.mime_type}")
    print(f"Erkannt via: {file_type.detection_method}")
    print(f"Kategorie: {file_type.category}")
    print(f"Processor: {file_type.processor}")
    print()

    # 2. Text extrahieren
    if file_type.processor in ["tika", "tika_html"]:
        print("Extrahiere Text...")
        text, fmt = extract_text_enhanced(filepath)
        print(f"Format: {fmt}")
        print(f"Länge: {len(text)} Zeichen")
        print()
        print("Erste 500 Zeichen:")
        print("-" * 50)
        print(text[:500])
