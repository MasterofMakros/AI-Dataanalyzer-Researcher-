"""
Neural Vault Context Header System
===================================

Fügt jedem Chunk einen strukturierten Header hinzu, damit das LLM
den Kontext (Dateityp, Quelle, Position) versteht.

Übernahme aus Gemini-Analyse vom 2025-12-28.

Usage:
    from utils.context_header import wrap_chunk, SourceType

    wrapped = wrap_chunk(
        text="Rechnungsbetrag: 127,45€",
        source_type=SourceType.PDF,
        filename="Telekom_Rechnung_2024.pdf",
        location={"page": 2, "lines": "15-18"}
    )
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class SourceType(Enum):
    """Unterstützte Quellentypen für Context Header."""
    PDF = "PDF Document"
    SPREADSHEET = "Spreadsheet"
    EMAIL = "Email"
    IMAGE = "Image (OCR)"
    AUDIO = "Audio Transcript"
    VIDEO = "Video Transcript"
    TEXT = "Text Document"
    CODE = "Source Code"
    ARCHIVE = "Archive Contents"
    UNKNOWN = "Unknown"


@dataclass
class ChunkLocation:
    """Positionsinformation für einen Chunk."""
    # Für PDFs
    page: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    # Für Audio/Video
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None

    # Für Spreadsheets
    sheet_name: Optional[str] = None
    cell_range: Optional[str] = None

    # Für Images
    bounding_box: Optional[Dict[str, int]] = None  # x, y, width, height

    def to_string(self) -> str:
        """Formatiert die Location als lesbaren String."""
        parts = []

        if self.page is not None:
            parts.append(f"Page {self.page}")
        if self.line_start is not None:
            if self.line_end and self.line_end != self.line_start:
                parts.append(f"Lines {self.line_start}-{self.line_end}")
            else:
                parts.append(f"Line {self.line_start}")
        if self.timestamp_start is not None:
            start_fmt = format_timestamp(self.timestamp_start)
            if self.timestamp_end:
                end_fmt = format_timestamp(self.timestamp_end)
                parts.append(f"Time {start_fmt}-{end_fmt}")
            else:
                parts.append(f"Time {start_fmt}")
        if self.sheet_name:
            parts.append(f"Sheet: {self.sheet_name}")
        if self.cell_range:
            parts.append(f"Cells: {self.cell_range}")

        return " | ".join(parts) if parts else "Full Document"


def format_timestamp(seconds: float) -> str:
    """Formatiert Sekunden als HH:MM:SS oder MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def detect_source_type(filename: str, mime_type: Optional[str] = None) -> SourceType:
    """Erkennt den SourceType basierend auf Dateiname oder MIME-Type."""
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    # Extension-basierte Erkennung
    ext_mapping = {
        # PDF
        "pdf": SourceType.PDF,
        # Spreadsheets
        "xlsx": SourceType.SPREADSHEET,
        "xls": SourceType.SPREADSHEET,
        "csv": SourceType.SPREADSHEET,
        "ods": SourceType.SPREADSHEET,
        # Email
        "eml": SourceType.EMAIL,
        "msg": SourceType.EMAIL,
        # Images
        "jpg": SourceType.IMAGE,
        "jpeg": SourceType.IMAGE,
        "png": SourceType.IMAGE,
        "tiff": SourceType.IMAGE,
        "bmp": SourceType.IMAGE,
        "webp": SourceType.IMAGE,
        # Audio
        "mp3": SourceType.AUDIO,
        "wav": SourceType.AUDIO,
        "flac": SourceType.AUDIO,
        "m4a": SourceType.AUDIO,
        "ogg": SourceType.AUDIO,
        # Video
        "mp4": SourceType.VIDEO,
        "mkv": SourceType.VIDEO,
        "avi": SourceType.VIDEO,
        "mov": SourceType.VIDEO,
        "webm": SourceType.VIDEO,
        # Text
        "txt": SourceType.TEXT,
        "md": SourceType.TEXT,
        "rtf": SourceType.TEXT,
        "docx": SourceType.TEXT,
        "doc": SourceType.TEXT,
        # Code
        "py": SourceType.CODE,
        "js": SourceType.CODE,
        "ts": SourceType.CODE,
        "java": SourceType.CODE,
        "cpp": SourceType.CODE,
        "c": SourceType.CODE,
        "go": SourceType.CODE,
        "rs": SourceType.CODE,
        # Archive
        "zip": SourceType.ARCHIVE,
        "rar": SourceType.ARCHIVE,
        "7z": SourceType.ARCHIVE,
        "tar": SourceType.ARCHIVE,
        "gz": SourceType.ARCHIVE,
    }

    return ext_mapping.get(ext, SourceType.UNKNOWN)


def wrap_chunk(
    text: str,
    source_type: SourceType,
    filename: str,
    location: Optional[ChunkLocation] = None,
    confidence: Optional[float] = None,
    category: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Umwickelt einen Text-Chunk mit einem strukturierten Context Header.

    Args:
        text: Der eigentliche Textinhalt
        source_type: Typ der Quelle (PDF, Audio, etc.)
        filename: Name der Quelldatei
        location: Position innerhalb der Datei
        confidence: Konfidenz der Extraktion (0.0-1.0)
        category: Kategorie der Datei
        extra_metadata: Zusätzliche Metadaten

    Returns:
        Text mit Context Header im Format:
        [SOURCE: Type | Filename | Location | Metadata]
        <content>
        [/SOURCE]
    """
    # Header-Teile zusammenbauen
    header_parts = [
        f"Type: {source_type.value}",
        f"File: {filename}"
    ]

    if location:
        loc_str = location.to_string()
        if loc_str != "Full Document":
            header_parts.append(f"Location: {loc_str}")

    if category:
        header_parts.append(f"Category: {category}")

    if confidence is not None:
        header_parts.append(f"Confidence: {confidence:.0%}")

    # Extra Metadata
    if extra_metadata:
        for key, value in extra_metadata.items():
            if value is not None:
                header_parts.append(f"{key}: {value}")

    # Zusammenbauen
    header = " | ".join(header_parts)

    return f"[SOURCE: {header}]\n{text}\n[/SOURCE]"


def unwrap_chunk(wrapped_text: str) -> tuple[str, Dict[str, Any]]:
    """
    Extrahiert den Originaltext und Metadaten aus einem gewrappten Chunk.

    Args:
        wrapped_text: Text mit Context Header

    Returns:
        Tuple aus (originaltext, metadata_dict)
    """
    import re

    # Pattern für [SOURCE: ...] ... [/SOURCE]
    pattern = r'\[SOURCE:\s*([^\]]+)\]\n(.*?)\n\[/SOURCE\]'
    match = re.search(pattern, wrapped_text, re.DOTALL)

    if not match:
        # Kein Header gefunden, Originaltext zurückgeben
        return wrapped_text, {}

    header_str = match.group(1)
    content = match.group(2)

    # Header parsen
    metadata = {}
    for part in header_str.split(" | "):
        if ": " in part:
            key, value = part.split(": ", 1)
            metadata[key.strip()] = value.strip()

    return content, metadata


def create_chunk_for_rag(
    text: str,
    filename: str,
    mime_type: Optional[str] = None,
    page: Optional[int] = None,
    timestamp_start: Optional[float] = None,
    timestamp_end: Optional[float] = None,
    sheet_name: Optional[str] = None,
    category: Optional[str] = None,
    confidence: Optional[float] = None
) -> str:
    """
    Convenience-Funktion: Erstellt einen RAG-ready Chunk mit allen Infos.

    Dies ist die Hauptfunktion für die Ingestion-Pipeline.
    """
    source_type = detect_source_type(filename, mime_type)

    location = ChunkLocation(
        page=page,
        timestamp_start=timestamp_start,
        timestamp_end=timestamp_end,
        sheet_name=sheet_name
    )

    return wrap_chunk(
        text=text,
        source_type=source_type,
        filename=filename,
        location=location,
        confidence=confidence,
        category=category
    )


# Beispiel-Nutzung
if __name__ == "__main__":
    # Beispiel 1: PDF
    pdf_chunk = create_chunk_for_rag(
        text="Rechnungsbetrag: 127,45 EUR\nFällig am: 15.01.2025",
        filename="Telekom_Rechnung_2024-12.pdf",
        page=1,
        category="Finanzen",
        confidence=0.95
    )
    print("PDF Chunk:")
    print(pdf_chunk)
    print()

    # Beispiel 2: Audio
    audio_chunk = create_chunk_for_rag(
        text="Die Netzabdeckung in Ihrer Region ist momentan eingeschränkt.",
        filename="Anruf_Telekom_2024-11-10.mp3",
        timestamp_start=154.5,
        timestamp_end=162.3,
        category="Kommunikation",
        confidence=0.89
    )
    print("Audio Chunk:")
    print(audio_chunk)
    print()

    # Beispiel 3: Excel
    excel_chunk = create_chunk_for_rag(
        text="| Monat | Betrag |\n| Januar | 500€ |\n| Februar | 750€ |",
        filename="Budget_2024.xlsx",
        sheet_name="Q1",
        category="Finanzen",
        confidence=0.98
    )
    print("Excel Chunk:")
    print(excel_chunk)
    print()

    # Unwrap Test
    text, meta = unwrap_chunk(pdf_chunk)
    print("Unwrapped:")
    print(f"  Text: {text[:50]}...")
    print(f"  Metadata: {meta}")
