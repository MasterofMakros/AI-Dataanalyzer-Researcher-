"""
Neural Vault Parser Routing Configuration
==========================================

Docling-First Strategie basierend auf Benchmark-Ergebnissen (Procycons 2025):
- Docling: 97.9% Table Accuracy
- Tika: 75% Table Accuracy

Usage:
    from config.parser_routing import get_parser, ParserType
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class ParserType(Enum):
    """Verfügbare Parser."""
    DOCLING = "docling"      # Strukturierte Dokumente (Tables, Layouts)
    TIKA = "tika"            # Universal Fallback (1400+ Formate)
    SURYA = "surya"          # OCR (97.7% Accuracy)
    WHISPERX = "whisperx"    # Audio Transcription
    FFMPEG = "ffmpeg"        # Video/Audio Extraction
    ARCHIVE = "archive"      # ZIP, RAR, 7z


@dataclass
class ParserConfig:
    """Konfiguration für einen Parser."""
    parser_type: ParserType
    url: str
    timeout: int = 120
    supports_ocr: bool = False
    supports_tables: bool = False
    gpu_required: bool = False


# =============================================================================
# PARSER ENDPOINTS
# =============================================================================

PARSER_CONFIGS = {
    ParserType.DOCLING: ParserConfig(
        parser_type=ParserType.DOCLING,
        url="http://localhost:8005/process/document",
        timeout=180,
        supports_ocr=True,
        supports_tables=True,
        gpu_required=True,
    ),
    ParserType.TIKA: ParserConfig(
        parser_type=ParserType.TIKA,
        url="http://localhost:9998/tika",
        timeout=60,
        supports_ocr=False,
        supports_tables=False,
        gpu_required=False,
    ),
    ParserType.SURYA: ParserConfig(
        parser_type=ParserType.SURYA,
        url="http://localhost:9999/ocr",
        timeout=120,
        supports_ocr=True,
        supports_tables=True,
        gpu_required=True,
    ),
    ParserType.WHISPERX: ParserConfig(
        parser_type=ParserType.WHISPERX,
        url="http://localhost:9000/transcribe",
        timeout=600,
        supports_ocr=False,
        supports_tables=False,
        gpu_required=True,
    ),
}


# =============================================================================
# DOCLING-FIRST ROUTING
# =============================================================================

# Format → Primary Parser
# Benchmark: Docling 97.9% vs Tika 75% auf Tables
PARSER_ROUTING: Dict[str, ParserType] = {
    # =========================================================================
    # DOCLING-FIRST (Strukturierte Dokumente mit Tables)
    # =========================================================================
    ".pdf": ParserType.DOCLING,
    ".docx": ParserType.DOCLING,
    ".pptx": ParserType.DOCLING,
    ".xlsx": ParserType.DOCLING,

    # =========================================================================
    # TIKA (Legacy Office + Exotische Formate)
    # =========================================================================
    ".doc": ParserType.TIKA,
    ".xls": ParserType.TIKA,
    ".ppt": ParserType.TIKA,
    ".rtf": ParserType.TIKA,

    # Email
    ".eml": ParserType.TIKA,
    ".msg": ParserType.TIKA,
    ".mbox": ParserType.TIKA,

    # Text
    ".txt": ParserType.TIKA,
    ".md": ParserType.TIKA,
    ".html": ParserType.TIKA,
    ".htm": ParserType.TIKA,
    ".xml": ParserType.TIKA,
    ".json": ParserType.TIKA,
    ".csv": ParserType.TIKA,

    # E-Books
    ".epub": ParserType.TIKA,
    ".mobi": ParserType.TIKA,

    # =========================================================================
    # SURYA OCR (Bilder mit Text)
    # =========================================================================
    ".jpg": ParserType.SURYA,
    ".jpeg": ParserType.SURYA,
    ".png": ParserType.SURYA,
    ".tiff": ParserType.SURYA,
    ".tif": ParserType.SURYA,
    ".bmp": ParserType.SURYA,
    ".webp": ParserType.SURYA,

    # =========================================================================
    # WHISPERX (Audio)
    # =========================================================================
    ".mp3": ParserType.WHISPERX,
    ".wav": ParserType.WHISPERX,
    ".m4a": ParserType.WHISPERX,
    ".flac": ParserType.WHISPERX,
    ".ogg": ParserType.WHISPERX,
    ".wma": ParserType.WHISPERX,
    ".aac": ParserType.WHISPERX,

    # =========================================================================
    # VIDEO (Audio-Track Extraktion)
    # =========================================================================
    ".mp4": ParserType.WHISPERX,
    ".mkv": ParserType.WHISPERX,
    ".avi": ParserType.WHISPERX,
    ".mov": ParserType.WHISPERX,
    ".webm": ParserType.WHISPERX,
    ".wmv": ParserType.WHISPERX,

    # =========================================================================
    # ARCHIVE (Extraction, no parsing)
    # =========================================================================
    ".zip": ParserType.ARCHIVE,
    ".rar": ParserType.ARCHIVE,
    ".7z": ParserType.ARCHIVE,
    ".tar": ParserType.ARCHIVE,
    ".gz": ParserType.ARCHIVE,
}


# Fallback für unbekannte Formate
DEFAULT_PARSER = ParserType.TIKA


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def get_parser(extension: str) -> ParserType:
    """
    Ermittelt den optimalen Parser für eine Dateierweiterung.

    Args:
        extension: Dateierweiterung (mit oder ohne Punkt)

    Returns:
        ParserType für diese Extension
    """
    ext = extension.lower()
    if not ext.startswith("."):
        ext = f".{ext}"

    return PARSER_ROUTING.get(ext, DEFAULT_PARSER)


def get_parser_config(extension: str) -> ParserConfig:
    """
    Holt die Parser-Konfiguration für eine Extension.

    Args:
        extension: Dateierweiterung

    Returns:
        ParserConfig mit URL, Timeout, etc.
    """
    parser_type = get_parser(extension)
    return PARSER_CONFIGS.get(parser_type, PARSER_CONFIGS[ParserType.TIKA])


def get_fallback_chain(extension: str) -> List[ParserType]:
    """
    Gibt die Fallback-Kette für eine Extension zurück.

    Z.B. für PDF: [DOCLING, TIKA]
    Wenn Docling fehlschlägt, wird Tika versucht.
    """
    primary = get_parser(extension)

    chains = {
        ParserType.DOCLING: [ParserType.DOCLING, ParserType.TIKA],
        ParserType.SURYA: [ParserType.SURYA, ParserType.TIKA],
        ParserType.WHISPERX: [ParserType.WHISPERX],  # Kein Fallback
        ParserType.TIKA: [ParserType.TIKA],
        ParserType.ARCHIVE: [ParserType.ARCHIVE],
    }

    return chains.get(primary, [ParserType.TIKA])


def needs_gpu(extension: str) -> bool:
    """Prüft ob GPU für diese Extension benötigt wird."""
    config = get_parser_config(extension)
    return config.gpu_required


def supports_tables(extension: str) -> bool:
    """Prüft ob Tabellen-Extraktion unterstützt wird."""
    config = get_parser_config(extension)
    return config.supports_tables


# =============================================================================
# STATISTICS
# =============================================================================

def get_routing_stats() -> dict:
    """
    Statistiken über das Routing.
    """
    stats = {parser.value: 0 for parser in ParserType}

    for ext, parser in PARSER_ROUTING.items():
        stats[parser.value] += 1

    return {
        "total_extensions": len(PARSER_ROUTING),
        "by_parser": stats,
        "docling_first_extensions": [
            ext for ext, p in PARSER_ROUTING.items()
            if p == ParserType.DOCLING
        ],
        "gpu_required_extensions": [
            ext for ext in PARSER_ROUTING.keys()
            if needs_gpu(ext)
        ],
    }
