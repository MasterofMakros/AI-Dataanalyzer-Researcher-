"""
Neural Vault Universal Format Registry
======================================

Vollständige Registry aller bekannten Dateiformate mit:
- MIME-Type Mapping
- Magic Bytes (Datei-Signatur)
- Processor-Zuordnung
- Extraktions-Strategie

Abdeckung: 200+ Formate in 15 Kategorien
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class ProcessorType(str, Enum):
    """Verfügbare Processor-Typen."""
    # Text Extraction
    TIKA = "tika"                      # Apache Tika (universell)
    TIKA_HTML = "tika_html"            # Tika mit HTML-Output
    DOCLING = "docling"                # Docling (komplexe PDFs)
    PANDOC = "pandoc"                  # Pandoc (Markup-Konvertierung)

    # OCR
    TESSERACT = "tesseract"            # Tesseract OCR
    PADDLEOCR = "paddleocr"            # PaddleOCR (besser für Asiatisch)
    SURYA = "surya"                    # Surya (beste Qualität)

    # Audio/Video
    WHISPER_FAST = "whisper_fast"      # Whisper Base (schnell)
    WHISPER_ACCURATE = "whisper_accurate"  # Whisper Large-v3 (genau)
    FFMPEG = "ffmpeg"                  # FFmpeg (Metadaten)
    FFMPEG_EXTRACT = "ffmpeg_extract"  # FFmpeg Audio-Extraktion

    # Spezialformate
    PARSER_EMAIL = "parser_email"      # E-Mail Parser
    PARSER_ARCHIVE = "parser_archive"  # Archiv-Listing (7-Zip)
    PARSER_3D = "parser_3d"            # 3D-Modelle (trimesh)
    PARSER_CAD = "parser_cad"          # CAD-Dateien
    PARSER_CODE = "parser_code"        # Source Code
    PARSER_DATABASE = "parser_database"  # Datenbanken
    PARSER_GIS = "parser_gis"          # Geodaten
    PARSER_SCIENTIFIC = "parser_scientific"  # Wissenschaftliche Formate
    PARSER_EBOOK = "parser_ebook"      # E-Books
    PARSER_FONT = "parser_font"        # Schriftarten
    PARSER_GAME = "parser_game"        # Spieldaten
    PARSER_CRYPTO = "parser_crypto"    # Verschlüsselte Dateien
    PARSER_BINARY = "parser_binary"    # Binäranalyse (Fallback)

    # Metadata Only
    EXIFTOOL = "exiftool"              # EXIF/Metadata
    MEDIAINFO = "mediainfo"            # Media Metadata

    # Fallback
    STRINGS = "strings"                # Unix strings (Fallback)
    SKIP = "skip"                      # Überspringen
    MANUAL = "manual"                  # Manuelle Prüfung


class ExtractionStrategy(str, Enum):
    """Wie der Inhalt extrahiert wird."""
    TEXT = "text"              # Reiner Text
    HTML_TO_MD = "html_to_md"  # HTML → Markdown
    OCR = "ocr"                # Bilderkennung
    TRANSCRIBE = "transcribe"  # Audio → Text
    METADATA = "metadata"      # Nur Metadaten
    LISTING = "listing"        # Dateiliste (Archive)
    STRUCTURE = "structure"    # Strukturierte Daten
    BINARY = "binary"          # Binäranalyse
    SKIP = "skip"              # Überspringen


@dataclass
class FormatSpec:
    """Spezifikation eines Dateiformats."""
    extension: str
    name: str
    mime_types: List[str]
    category: str
    processor: ProcessorType
    strategy: ExtractionStrategy
    magic_bytes: Optional[bytes] = None
    magic_offset: int = 0
    fallback_processor: Optional[ProcessorType] = None
    requires_gpu: bool = False
    typical_size_mb: float = 1.0
    priority_boost: int = 0  # Extra Priority
    notes: str = ""


# =============================================================================
# FORMAT REGISTRY - 200+ Formate
# =============================================================================

FORMAT_REGISTRY: Dict[str, FormatSpec] = {}


def register(spec: FormatSpec):
    """Registriert ein Format."""
    FORMAT_REGISTRY[spec.extension.lower()] = spec


# =============================================================================
# KATEGORIE 1: DOKUMENTE (30 Formate)
# =============================================================================

# PDF
register(FormatSpec(
    extension="pdf",
    name="Portable Document Format",
    mime_types=["application/pdf"],
    category="documents",
    processor=ProcessorType.TIKA_HTML,
    strategy=ExtractionStrategy.HTML_TO_MD,
    magic_bytes=b"%PDF",
    fallback_processor=ProcessorType.DOCLING,
    typical_size_mb=2.0,
    priority_boost=15,
    notes="Dual-Path: Tika für Text-PDFs, Docling für gescannte"
))

# Microsoft Office - Modern
for ext, name, mime in [
    ("docx", "Word Document", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("xlsx", "Excel Spreadsheet", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("pptx", "PowerPoint Presentation", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
]:
    register(FormatSpec(
        extension=ext,
        name=f"Microsoft {name}",
        mime_types=[mime],
        category="documents",
        processor=ProcessorType.TIKA_HTML,
        strategy=ExtractionStrategy.HTML_TO_MD,
        magic_bytes=b"PK\x03\x04",  # ZIP-basiert
        priority_boost=15
    ))

# Microsoft Office - Legacy
for ext, name, mime in [
    ("doc", "Word Document (Legacy)", "application/msword"),
    ("xls", "Excel Spreadsheet (Legacy)", "application/vnd.ms-excel"),
    ("ppt", "PowerPoint (Legacy)", "application/vnd.ms-powerpoint"),
]:
    register(FormatSpec(
        extension=ext,
        name=f"Microsoft {name}",
        mime_types=[mime],
        category="documents",
        processor=ProcessorType.TIKA,
        strategy=ExtractionStrategy.TEXT,
        magic_bytes=b"\xd0\xcf\x11\xe0",  # OLE2
        priority_boost=12
    ))

# OpenDocument Format
for ext, name, mime in [
    ("odt", "OpenDocument Text", "application/vnd.oasis.opendocument.text"),
    ("ods", "OpenDocument Spreadsheet", "application/vnd.oasis.opendocument.spreadsheet"),
    ("odp", "OpenDocument Presentation", "application/vnd.oasis.opendocument.presentation"),
    ("odg", "OpenDocument Graphics", "application/vnd.oasis.opendocument.graphics"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="documents",
        processor=ProcessorType.TIKA_HTML,
        strategy=ExtractionStrategy.HTML_TO_MD,
        magic_bytes=b"PK\x03\x04"
    ))

# Rich Text & Plain Text
register(FormatSpec(
    extension="rtf",
    name="Rich Text Format",
    mime_types=["application/rtf", "text/rtf"],
    category="documents",
    processor=ProcessorType.TIKA,
    strategy=ExtractionStrategy.TEXT,
    magic_bytes=b"{\\rtf"
))

register(FormatSpec(
    extension="txt",
    name="Plain Text",
    mime_types=["text/plain"],
    category="documents",
    processor=ProcessorType.TIKA,
    strategy=ExtractionStrategy.TEXT,
    priority_boost=5
))

# Weitere Dokumentformate
for ext, name, mime, proc in [
    ("csv", "Comma-Separated Values", "text/csv", ProcessorType.TIKA),
    ("tsv", "Tab-Separated Values", "text/tab-separated-values", ProcessorType.TIKA),
    ("xml", "XML Document", "application/xml", ProcessorType.TIKA),
    ("json", "JSON Document", "application/json", ProcessorType.TIKA),
    ("yaml", "YAML Document", "application/x-yaml", ProcessorType.TIKA),
    ("yml", "YAML Document", "application/x-yaml", ProcessorType.TIKA),
    ("html", "HTML Document", "text/html", ProcessorType.TIKA_HTML),
    ("htm", "HTML Document", "text/html", ProcessorType.TIKA_HTML),
    ("xhtml", "XHTML Document", "application/xhtml+xml", ProcessorType.TIKA_HTML),
    ("mhtml", "MHTML Archive", "message/rfc822", ProcessorType.TIKA),
    ("tex", "LaTeX Document", "application/x-latex", ProcessorType.PANDOC),
    ("latex", "LaTeX Document", "application/x-latex", ProcessorType.PANDOC),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="documents",
        processor=proc,
        strategy=ExtractionStrategy.TEXT if proc != ProcessorType.TIKA_HTML else ExtractionStrategy.HTML_TO_MD
    ))

# Apple iWork
for ext, name, mime in [
    ("pages", "Apple Pages", "application/vnd.apple.pages"),
    ("numbers", "Apple Numbers", "application/vnd.apple.numbers"),
    ("key", "Apple Keynote", "application/vnd.apple.keynote"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="documents",
        processor=ProcessorType.TIKA,
        strategy=ExtractionStrategy.TEXT,
        magic_bytes=b"PK\x03\x04"
    ))


# =============================================================================
# KATEGORIE 2: E-BOOKS (12 Formate)
# =============================================================================

register(FormatSpec(
    extension="epub",
    name="Electronic Publication",
    mime_types=["application/epub+zip"],
    category="ebooks",
    processor=ProcessorType.TIKA_HTML,
    strategy=ExtractionStrategy.HTML_TO_MD,
    magic_bytes=b"PK\x03\x04",
    priority_boost=10
))

register(FormatSpec(
    extension="mobi",
    name="Mobipocket E-Book",
    mime_types=["application/x-mobipocket-ebook"],
    category="ebooks",
    processor=ProcessorType.PARSER_EBOOK,
    strategy=ExtractionStrategy.TEXT,
    magic_bytes=b"BOOKMOBI"
))

register(FormatSpec(
    extension="azw",
    name="Amazon Kindle",
    mime_types=["application/vnd.amazon.ebook"],
    category="ebooks",
    processor=ProcessorType.PARSER_EBOOK,
    strategy=ExtractionStrategy.TEXT
))

register(FormatSpec(
    extension="azw3",
    name="Amazon Kindle Format 8",
    mime_types=["application/vnd.amazon.ebook"],
    category="ebooks",
    processor=ProcessorType.PARSER_EBOOK,
    strategy=ExtractionStrategy.TEXT
))

for ext, name in [
    ("fb2", "FictionBook 2"),
    ("djvu", "DjVu Document"),
    ("cbz", "Comic Book Archive (ZIP)"),
    ("cbr", "Comic Book Archive (RAR)"),
    ("cb7", "Comic Book Archive (7z)"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[f"application/x-{ext}"],
        category="ebooks",
        processor=ProcessorType.PARSER_EBOOK if ext.startswith("cb") else ProcessorType.TIKA,
        strategy=ExtractionStrategy.TEXT if not ext.startswith("cb") else ExtractionStrategy.LISTING
    ))


# =============================================================================
# KATEGORIE 3: BILDER (25 Formate)
# =============================================================================

# Raster-Bilder mit OCR
for ext, name, mime, magic in [
    ("jpg", "JPEG Image", "image/jpeg", b"\xff\xd8\xff"),
    ("jpeg", "JPEG Image", "image/jpeg", b"\xff\xd8\xff"),
    ("png", "PNG Image", "image/png", b"\x89PNG\r\n\x1a\n"),
    ("gif", "GIF Image", "image/gif", b"GIF8"),
    ("bmp", "Bitmap Image", "image/bmp", b"BM"),
    ("tiff", "TIFF Image", "image/tiff", b"II*\x00"),
    ("tif", "TIFF Image", "image/tiff", b"II*\x00"),
    ("webp", "WebP Image", "image/webp", b"RIFF"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="images",
        processor=ProcessorType.TESSERACT,
        strategy=ExtractionStrategy.OCR,
        magic_bytes=magic,
        fallback_processor=ProcessorType.EXIFTOOL
    ))

# RAW-Formate (Kamera)
for ext, name in [
    ("raw", "Raw Image"),
    ("cr2", "Canon Raw 2"),
    ("cr3", "Canon Raw 3"),
    ("nef", "Nikon Raw"),
    ("arw", "Sony Raw"),
    ("dng", "Digital Negative"),
    ("orf", "Olympus Raw"),
    ("rw2", "Panasonic Raw"),
    ("pef", "Pentax Raw"),
    ("raf", "Fujifilm Raw"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[f"image/x-{ext}"],
        category="images_raw",
        processor=ProcessorType.EXIFTOOL,
        strategy=ExtractionStrategy.METADATA,
        notes="RAW-Bilder: Nur Metadaten extrahieren"
    ))

# Vektor-Grafiken
for ext, name, mime in [
    ("svg", "Scalable Vector Graphics", "image/svg+xml"),
    ("eps", "Encapsulated PostScript", "application/postscript"),
    ("ai", "Adobe Illustrator", "application/illustrator"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="images_vector",
        processor=ProcessorType.TIKA,
        strategy=ExtractionStrategy.TEXT
    ))

# Spezialformate
register(FormatSpec(
    extension="psd",
    name="Adobe Photoshop",
    mime_types=["image/vnd.adobe.photoshop"],
    category="images",
    processor=ProcessorType.EXIFTOOL,
    strategy=ExtractionStrategy.METADATA,
    magic_bytes=b"8BPS"
))

register(FormatSpec(
    extension="xcf",
    name="GIMP Image",
    mime_types=["image/x-xcf"],
    category="images",
    processor=ProcessorType.EXIFTOOL,
    strategy=ExtractionStrategy.METADATA,
    magic_bytes=b"gimp xcf"
))

register(FormatSpec(
    extension="ico",
    name="Icon File",
    mime_types=["image/x-icon"],
    category="images",
    processor=ProcessorType.EXIFTOOL,
    strategy=ExtractionStrategy.METADATA
))

register(FormatSpec(
    extension="exr",
    name="OpenEXR",
    mime_types=["image/x-exr"],
    category="images_hdr",
    processor=ProcessorType.EXIFTOOL,
    strategy=ExtractionStrategy.METADATA,
    magic_bytes=b"\x76\x2f\x31\x01",
    notes="HDR-Format für VFX"
))

register(FormatSpec(
    extension="heic",
    name="HEIF Image",
    mime_types=["image/heic"],
    category="images",
    processor=ProcessorType.TESSERACT,
    strategy=ExtractionStrategy.OCR,
    notes="Apple iOS Format"
))

register(FormatSpec(
    extension="heif",
    name="HEIF Image",
    mime_types=["image/heif"],
    category="images",
    processor=ProcessorType.TESSERACT,
    strategy=ExtractionStrategy.OCR
))

register(FormatSpec(
    extension="avif",
    name="AVIF Image",
    mime_types=["image/avif"],
    category="images",
    processor=ProcessorType.TESSERACT,
    strategy=ExtractionStrategy.OCR,
    notes="Modernes AV1-basiertes Format"
))


# =============================================================================
# KATEGORIE 4: AUDIO (20 Formate)
# =============================================================================

# Verlustbehaftete Formate
for ext, name, mime, magic in [
    ("mp3", "MP3 Audio", "audio/mpeg", b"\xff\xfb"),
    ("aac", "AAC Audio", "audio/aac", None),
    ("m4a", "MPEG-4 Audio", "audio/mp4", b"\x00\x00\x00"),
    ("wma", "Windows Media Audio", "audio/x-ms-wma", b"0&\xb2u"),
    ("ogg", "Ogg Vorbis", "audio/ogg", b"OggS"),
    ("opus", "Opus Audio", "audio/opus", b"OggS"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="audio",
        processor=ProcessorType.WHISPER_FAST,
        strategy=ExtractionStrategy.TRANSCRIBE,
        magic_bytes=magic,
        fallback_processor=ProcessorType.WHISPER_ACCURATE,
        requires_gpu=False,
        priority_boost=12,
        notes="Transkription via Whisper"
    ))

# Verlustfreie Formate
for ext, name, mime, magic in [
    ("wav", "WAV Audio", "audio/wav", b"RIFF"),
    ("flac", "FLAC Audio", "audio/flac", b"fLaC"),
    ("alac", "Apple Lossless", "audio/x-alac", None),
    ("aiff", "AIFF Audio", "audio/aiff", b"FORM"),
    ("ape", "Monkey's Audio", "audio/x-ape", b"MAC "),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="audio_lossless",
        processor=ProcessorType.WHISPER_FAST,
        strategy=ExtractionStrategy.TRANSCRIBE,
        magic_bytes=magic,
        fallback_processor=ProcessorType.WHISPER_ACCURATE,
        priority_boost=12
    ))

# MIDI & Spezialformate
register(FormatSpec(
    extension="mid",
    name="MIDI File",
    mime_types=["audio/midi"],
    category="audio_midi",
    processor=ProcessorType.FFMPEG,
    strategy=ExtractionStrategy.METADATA,
    magic_bytes=b"MThd",
    notes="MIDI: Keine Transkription möglich"
))

register(FormatSpec(
    extension="midi",
    name="MIDI File",
    mime_types=["audio/midi"],
    category="audio_midi",
    processor=ProcessorType.FFMPEG,
    strategy=ExtractionStrategy.METADATA,
    magic_bytes=b"MThd"
))

# Podcast/Hörbuch
register(FormatSpec(
    extension="m4b",
    name="M4B Audiobook",
    mime_types=["audio/mp4"],
    category="audio_book",
    processor=ProcessorType.WHISPER_ACCURATE,
    strategy=ExtractionStrategy.TRANSCRIBE,
    requires_gpu=True,
    priority_boost=10,
    notes="Hörbücher: Deep Path empfohlen"
))


# =============================================================================
# KATEGORIE 5: VIDEO (25 Formate)
# =============================================================================

# Gängige Videoformate
for ext, name, mime, magic in [
    ("mp4", "MPEG-4 Video", "video/mp4", b"\x00\x00\x00"),
    ("m4v", "MPEG-4 Video", "video/x-m4v", b"\x00\x00\x00"),
    ("mkv", "Matroska Video", "video/x-matroska", b"\x1a\x45\xdf\xa3"),
    ("webm", "WebM Video", "video/webm", b"\x1a\x45\xdf\xa3"),
    ("avi", "AVI Video", "video/x-msvideo", b"RIFF"),
    ("mov", "QuickTime Video", "video/quicktime", b"\x00\x00\x00"),
    ("wmv", "Windows Media Video", "video/x-ms-wmv", b"0&\xb2u"),
    ("flv", "Flash Video", "video/x-flv", b"FLV\x01"),
    ("mpg", "MPEG Video", "video/mpeg", b"\x00\x00\x01"),
    ("mpeg", "MPEG Video", "video/mpeg", b"\x00\x00\x01"),
    ("3gp", "3GPP Video", "video/3gpp", b"\x00\x00\x00"),
    ("3g2", "3GPP2 Video", "video/3gpp2", b"\x00\x00\x00"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="video",
        processor=ProcessorType.FFMPEG_EXTRACT,
        strategy=ExtractionStrategy.TRANSCRIBE,
        magic_bytes=magic,
        fallback_processor=ProcessorType.FFMPEG,
        requires_gpu=True,
        typical_size_mb=500,
        priority_boost=8,
        notes="Video: Audio extrahieren → Whisper"
    ))

# Professionelle Formate
for ext, name, mime in [
    ("mxf", "Material Exchange Format", "application/mxf"),
    ("ts", "MPEG Transport Stream", "video/mp2t"),
    ("m2ts", "Blu-ray MPEG-2 TS", "video/mp2t"),
    ("vob", "DVD Video Object", "video/dvd"),
    ("ogv", "Ogg Video", "video/ogg"),
    ("rm", "RealMedia", "application/vnd.rn-realmedia"),
    ("rmvb", "RealMedia VBR", "application/vnd.rn-realmedia-vbr"),
    ("divx", "DivX Video", "video/divx"),
    ("xvid", "XviD Video", "video/x-xvid"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="video",
        processor=ProcessorType.FFMPEG_EXTRACT,
        strategy=ExtractionStrategy.TRANSCRIBE,
        requires_gpu=True
    ))

# Screen Recording / Animation
register(FormatSpec(
    extension="gif",
    name="Animated GIF",
    mime_types=["image/gif"],
    category="video_animation",
    processor=ProcessorType.FFMPEG,
    strategy=ExtractionStrategy.METADATA,
    magic_bytes=b"GIF8"
))


# =============================================================================
# KATEGORIE 6: E-MAIL & KOMMUNIKATION (15 Formate)
# =============================================================================

register(FormatSpec(
    extension="eml",
    name="Email Message",
    mime_types=["message/rfc822"],
    category="email",
    processor=ProcessorType.PARSER_EMAIL,
    strategy=ExtractionStrategy.STRUCTURE,
    priority_boost=25,
    notes="Höchste Priorität: Kommunikation"
))

register(FormatSpec(
    extension="msg",
    name="Outlook Message",
    mime_types=["application/vnd.ms-outlook"],
    category="email",
    processor=ProcessorType.PARSER_EMAIL,
    strategy=ExtractionStrategy.STRUCTURE,
    magic_bytes=b"\xd0\xcf\x11\xe0",
    priority_boost=25
))

register(FormatSpec(
    extension="mbox",
    name="Mailbox File",
    mime_types=["application/mbox"],
    category="email",
    processor=ProcessorType.PARSER_EMAIL,
    strategy=ExtractionStrategy.STRUCTURE,
    priority_boost=25
))

register(FormatSpec(
    extension="pst",
    name="Outlook Data File",
    mime_types=["application/vnd.ms-outlook-pst"],
    category="email",
    processor=ProcessorType.PARSER_EMAIL,
    strategy=ExtractionStrategy.STRUCTURE,
    magic_bytes=b"!BDN",
    priority_boost=25,
    notes="Outlook-Archiv: Enthält viele E-Mails"
))

register(FormatSpec(
    extension="ost",
    name="Outlook Offline Storage",
    mime_types=["application/vnd.ms-outlook-ost"],
    category="email",
    processor=ProcessorType.PARSER_EMAIL,
    strategy=ExtractionStrategy.STRUCTURE,
    priority_boost=25
))

# Chat-Formate
for ext, name in [
    ("vcf", "vCard Contact"),
    ("ics", "iCalendar Event"),
    ("ical", "iCalendar Event"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=["text/vcard" if ext == "vcf" else "text/calendar"],
        category="contacts",
        processor=ProcessorType.TIKA,
        strategy=ExtractionStrategy.STRUCTURE,
        priority_boost=20
    ))


# =============================================================================
# KATEGORIE 7: ARCHIVE (20 Formate)
# =============================================================================

# Gängige Archive
for ext, name, mime, magic in [
    ("zip", "ZIP Archive", "application/zip", b"PK\x03\x04"),
    ("rar", "RAR Archive", "application/x-rar-compressed", b"Rar!\x1a\x07"),
    ("7z", "7-Zip Archive", "application/x-7z-compressed", b"7z\xbc\xaf'"),
    ("tar", "TAR Archive", "application/x-tar", None),
    ("gz", "Gzip Archive", "application/gzip", b"\x1f\x8b"),
    ("bz2", "Bzip2 Archive", "application/x-bzip2", b"BZh"),
    ("xz", "XZ Archive", "application/x-xz", b"\xfd7zXZ"),
    ("lz", "Lzip Archive", "application/x-lzip", b"LZIP"),
    ("lzma", "LZMA Archive", "application/x-lzma", None),
    ("zst", "Zstandard Archive", "application/zstd", b"(\xb5/\xfd"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="archive",
        processor=ProcessorType.PARSER_ARCHIVE,
        strategy=ExtractionStrategy.LISTING,
        magic_bytes=magic,
        notes="Archiv-Listing ohne Entpacken"
    ))

# Kombinierte Archive
for ext, name in [
    ("tgz", "Gzipped TAR"),
    ("tar.gz", "Gzipped TAR"),
    ("tar.bz2", "Bzipped TAR"),
    ("tar.xz", "XZ TAR"),
    ("tbz2", "Bzipped TAR"),
    ("txz", "XZ TAR"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=["application/x-compressed-tar"],
        category="archive",
        processor=ProcessorType.PARSER_ARCHIVE,
        strategy=ExtractionStrategy.LISTING
    ))

# Disk Images
for ext, name, mime in [
    ("iso", "ISO Disk Image", "application/x-iso9660-image"),
    ("img", "Disk Image", "application/x-raw-disk-image"),
    ("dmg", "macOS Disk Image", "application/x-apple-diskimage"),
    ("vhd", "Virtual Hard Disk", "application/x-vhd"),
    ("vhdx", "Virtual Hard Disk v2", "application/x-vhdx"),
    ("vmdk", "VMware Disk", "application/x-vmdk"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="disk_image",
        processor=ProcessorType.PARSER_ARCHIVE,
        strategy=ExtractionStrategy.LISTING,
        notes="Disk Image: Nur Listing, nicht mounten"
    ))


# =============================================================================
# KATEGORIE 8: SOURCE CODE (40 Formate)
# =============================================================================

# Programmiersprachen
code_formats = [
    # Sprache, Extension, MIME
    ("Python", "py", "text/x-python"),
    ("JavaScript", "js", "application/javascript"),
    ("TypeScript", "ts", "application/typescript"),
    ("Java", "java", "text/x-java-source"),
    ("C", "c", "text/x-c"),
    ("C++", "cpp", "text/x-c++"),
    ("C++", "cxx", "text/x-c++"),
    ("C Header", "h", "text/x-c"),
    ("C++ Header", "hpp", "text/x-c++"),
    ("C#", "cs", "text/x-csharp"),
    ("Go", "go", "text/x-go"),
    ("Rust", "rs", "text/x-rust"),
    ("Ruby", "rb", "text/x-ruby"),
    ("PHP", "php", "application/x-php"),
    ("Swift", "swift", "text/x-swift"),
    ("Kotlin", "kt", "text/x-kotlin"),
    ("Scala", "scala", "text/x-scala"),
    ("R", "r", "text/x-r"),
    ("Perl", "pl", "text/x-perl"),
    ("Lua", "lua", "text/x-lua"),
    ("Shell", "sh", "application/x-sh"),
    ("Batch", "bat", "application/x-msdos-program"),
    ("PowerShell", "ps1", "application/x-powershell"),
    ("SQL", "sql", "application/sql"),
    ("Groovy", "groovy", "text/x-groovy"),
    ("Dart", "dart", "application/dart"),
    ("Elixir", "ex", "text/x-elixir"),
    ("Erlang", "erl", "text/x-erlang"),
    ("Haskell", "hs", "text/x-haskell"),
    ("Clojure", "clj", "text/x-clojure"),
    ("F#", "fs", "text/x-fsharp"),
    ("OCaml", "ml", "text/x-ocaml"),
    ("Assembly", "asm", "text/x-asm"),
    ("COBOL", "cob", "text/x-cobol"),
    ("Fortran", "f90", "text/x-fortran"),
]

for lang, ext, mime in code_formats:
    register(FormatSpec(
        extension=ext,
        name=f"{lang} Source Code",
        mime_types=[mime],
        category="code",
        processor=ProcessorType.PARSER_CODE,
        strategy=ExtractionStrategy.TEXT,
        priority_boost=5,
        notes="Source Code: Syntax-aware Parsing"
    ))

# Markup & Config
for ext, name, mime in [
    ("md", "Markdown", "text/markdown"),
    ("markdown", "Markdown", "text/markdown"),
    ("rst", "reStructuredText", "text/x-rst"),
    ("adoc", "AsciiDoc", "text/asciidoc"),
    ("ini", "INI Config", "text/plain"),
    ("cfg", "Config File", "text/plain"),
    ("conf", "Config File", "text/plain"),
    ("toml", "TOML Config", "application/toml"),
    ("properties", "Properties File", "text/x-java-properties"),
    ("env", "Environment File", "text/plain"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="code_config",
        processor=ProcessorType.TIKA,
        strategy=ExtractionStrategy.TEXT
    ))


# =============================================================================
# KATEGORIE 9: DATENBANKEN (15 Formate)
# =============================================================================

for ext, name, mime in [
    ("sqlite", "SQLite Database", "application/x-sqlite3"),
    ("sqlite3", "SQLite Database", "application/x-sqlite3"),
    ("db", "Database File", "application/x-sqlite3"),
    ("mdb", "Access Database", "application/x-msaccess"),
    ("accdb", "Access Database", "application/x-msaccess"),
    ("dbf", "dBASE File", "application/x-dbf"),
    ("sql", "SQL Dump", "application/sql"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="database",
        processor=ProcessorType.PARSER_DATABASE,
        strategy=ExtractionStrategy.STRUCTURE,
        magic_bytes=b"SQLite format 3" if "sqlite" in ext else None,
        priority_boost=10,
        notes="Datenbank: Schema + Sample-Daten extrahieren"
    ))


# =============================================================================
# KATEGORIE 10: 3D-MODELLE (15 Formate)
# =============================================================================

for ext, name, mime in [
    ("obj", "Wavefront OBJ", "model/obj"),
    ("stl", "Stereolithography", "model/stl"),
    ("ply", "Polygon File Format", "model/ply"),
    ("fbx", "Autodesk FBX", "model/fbx"),
    ("gltf", "GL Transmission Format", "model/gltf+json"),
    ("glb", "GL Binary", "model/gltf-binary"),
    ("dae", "Collada", "model/vnd.collada+xml"),
    ("3ds", "3D Studio", "application/x-3ds"),
    ("blend", "Blender File", "application/x-blender"),
    ("max", "3ds Max", "application/x-3dsmax"),
    ("ma", "Maya ASCII", "application/x-maya"),
    ("mb", "Maya Binary", "application/x-maya"),
    ("c4d", "Cinema 4D", "application/x-c4d"),
    ("skp", "SketchUp", "application/x-sketchup"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="3d_model",
        processor=ProcessorType.PARSER_3D,
        strategy=ExtractionStrategy.STRUCTURE,
        notes="3D-Modell: Vertices, Faces, Materials extrahieren"
    ))


# =============================================================================
# KATEGORIE 11: CAD & ENGINEERING (12 Formate)
# =============================================================================

for ext, name, mime in [
    ("dwg", "AutoCAD Drawing", "application/acad"),
    ("dxf", "Drawing Exchange Format", "application/dxf"),
    ("dwf", "Design Web Format", "application/x-dwf"),
    ("step", "STEP CAD", "application/step"),
    ("stp", "STEP CAD", "application/step"),
    ("iges", "IGES CAD", "application/iges"),
    ("igs", "IGES CAD", "application/iges"),
    ("sat", "ACIS SAT", "application/sat"),
    ("ipt", "Inventor Part", "application/vnd.autodesk.inventor"),
    ("iam", "Inventor Assembly", "application/vnd.autodesk.inventor"),
    ("sldprt", "SolidWorks Part", "application/sldprt"),
    ("sldasm", "SolidWorks Assembly", "application/sldasm"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="cad",
        processor=ProcessorType.PARSER_CAD,
        strategy=ExtractionStrategy.STRUCTURE,
        notes="CAD: Layerliste, Dimensionen extrahieren"
    ))


# =============================================================================
# KATEGORIE 12: GIS & GEODATEN (10 Formate)
# =============================================================================

for ext, name, mime in [
    ("shp", "Shapefile", "application/x-shapefile"),
    ("shx", "Shapefile Index", "application/x-shapefile"),
    ("dbf", "Shapefile Attributes", "application/x-dbf"),
    ("geojson", "GeoJSON", "application/geo+json"),
    ("kml", "Keyhole Markup", "application/vnd.google-earth.kml+xml"),
    ("kmz", "Keyhole Markup (ZIP)", "application/vnd.google-earth.kmz"),
    ("gpx", "GPS Exchange Format", "application/gpx+xml"),
    ("osm", "OpenStreetMap", "application/x-osm"),
    ("pbf", "OSM Protobuf", "application/x-protobuf"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="gis",
        processor=ProcessorType.PARSER_GIS,
        strategy=ExtractionStrategy.STRUCTURE,
        notes="Geodaten: Koordinaten, Features extrahieren"
    ))


# =============================================================================
# KATEGORIE 13: WISSENSCHAFTLICHE FORMATE (15 Formate)
# =============================================================================

for ext, name, mime, proc in [
    ("mat", "MATLAB Data", "application/x-matlab-data", ProcessorType.PARSER_SCIENTIFIC),
    ("nc", "NetCDF", "application/x-netcdf", ProcessorType.PARSER_SCIENTIFIC),
    ("hdf", "HDF4", "application/x-hdf", ProcessorType.PARSER_SCIENTIFIC),
    ("hdf5", "HDF5", "application/x-hdf5", ProcessorType.PARSER_SCIENTIFIC),
    ("h5", "HDF5", "application/x-hdf5", ProcessorType.PARSER_SCIENTIFIC),
    ("fits", "FITS Astronomy", "application/fits", ProcessorType.PARSER_SCIENTIFIC),
    ("fit", "FITS Astronomy", "application/fits", ProcessorType.PARSER_SCIENTIFIC),
    ("npy", "NumPy Array", "application/x-numpy", ProcessorType.PARSER_SCIENTIFIC),
    ("npz", "NumPy Archive", "application/x-numpy", ProcessorType.PARSER_SCIENTIFIC),
    ("pickle", "Python Pickle", "application/x-python-pickle", ProcessorType.PARSER_SCIENTIFIC),
    ("pkl", "Python Pickle", "application/x-python-pickle", ProcessorType.PARSER_SCIENTIFIC),
    ("parquet", "Apache Parquet", "application/x-parquet", ProcessorType.PARSER_SCIENTIFIC),
    ("feather", "Apache Feather", "application/x-feather", ProcessorType.PARSER_SCIENTIFIC),
    ("arrow", "Apache Arrow", "application/x-arrow", ProcessorType.PARSER_SCIENTIFIC),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="scientific",
        processor=proc,
        strategy=ExtractionStrategy.STRUCTURE,
        notes="Wissenschaftlich: Shape, Dtype, Sample-Daten"
    ))


# =============================================================================
# KATEGORIE 14: SCHRIFTARTEN (8 Formate)
# =============================================================================

for ext, name, mime in [
    ("ttf", "TrueType Font", "font/ttf"),
    ("otf", "OpenType Font", "font/otf"),
    ("woff", "Web Open Font Format", "font/woff"),
    ("woff2", "Web Open Font Format 2", "font/woff2"),
    ("eot", "Embedded OpenType", "application/vnd.ms-fontobject"),
    ("pfb", "PostScript Font", "application/x-font-pfb"),
    ("pfm", "PostScript Font Metrics", "application/x-font-pfm"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="font",
        processor=ProcessorType.PARSER_FONT,
        strategy=ExtractionStrategy.METADATA,
        notes="Font: Name, Glyphs, Metrics extrahieren"
    ))


# =============================================================================
# KATEGORIE 15: SPEZIAL & GAME-FORMATE (20 Formate)
# =============================================================================

# Torrents
register(FormatSpec(
    extension="torrent",
    name="BitTorrent Metainfo",
    mime_types=["application/x-bittorrent"],
    category="torrent",
    processor=ProcessorType.PARSER_BINARY,
    strategy=ExtractionStrategy.STRUCTURE,
    magic_bytes=b"d8:announce",
    priority_boost=5,
    notes="Torrent: Dateiliste, Tracker extrahieren"
))

# Untertitel
for ext, name, mime in [
    ("srt", "SubRip Subtitles", "application/x-subrip"),
    ("ass", "Advanced SubStation", "text/x-ass"),
    ("ssa", "SubStation Alpha", "text/x-ssa"),
    ("vtt", "WebVTT", "text/vtt"),
    ("sub", "MicroDVD Subtitles", "text/x-sub"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="subtitle",
        processor=ProcessorType.TIKA,
        strategy=ExtractionStrategy.TEXT,
        priority_boost=10,
        notes="Untertitel: Direkter Text"
    ))

# APK/IPA (Mobile Apps)
register(FormatSpec(
    extension="apk",
    name="Android Package",
    mime_types=["application/vnd.android.package-archive"],
    category="app_package",
    processor=ProcessorType.PARSER_ARCHIVE,
    strategy=ExtractionStrategy.STRUCTURE,
    magic_bytes=b"PK\x03\x04",
    notes="APK: Manifest, Permissions extrahieren"
))

register(FormatSpec(
    extension="ipa",
    name="iOS App Package",
    mime_types=["application/x-ios-app"],
    category="app_package",
    processor=ProcessorType.PARSER_ARCHIVE,
    strategy=ExtractionStrategy.STRUCTURE,
    magic_bytes=b"PK\x03\x04"
))

# Executable (nur Metadaten)
for ext, name, mime, magic in [
    ("exe", "Windows Executable", "application/x-msdownload", b"MZ"),
    ("dll", "Windows Library", "application/x-msdownload", b"MZ"),
    ("so", "Linux Shared Object", "application/x-sharedlib", b"\x7fELF"),
    ("dylib", "macOS Library", "application/x-mach-binary", b"\xcf\xfa\xed\xfe"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=[mime],
        category="executable",
        processor=ProcessorType.EXIFTOOL,
        strategy=ExtractionStrategy.METADATA,
        magic_bytes=magic,
        notes="Executable: Nur Metadaten, kein Code-Analyse"
    ))

# Verschlüsselte Dateien
for ext, name in [
    ("gpg", "GPG Encrypted"),
    ("pgp", "PGP Encrypted"),
    ("asc", "ASCII Armored"),
]:
    register(FormatSpec(
        extension=ext,
        name=name,
        mime_types=["application/pgp-encrypted"],
        category="encrypted",
        processor=ProcessorType.SKIP,
        strategy=ExtractionStrategy.SKIP,
        notes="Verschlüsselt: Überspringen ohne Schlüssel"
    ))


# =============================================================================
# FALLBACK FÜR UNBEKANNTE FORMATE
# =============================================================================

register(FormatSpec(
    extension="*",
    name="Unknown Format",
    mime_types=["application/octet-stream"],
    category="unknown",
    processor=ProcessorType.STRINGS,
    strategy=ExtractionStrategy.BINARY,
    fallback_processor=ProcessorType.SKIP,
    notes="Fallback: strings-Extraktion versuchen"
))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_format_spec(extension: str) -> FormatSpec:
    """Gibt FormatSpec für eine Extension zurück."""
    ext = extension.lower().lstrip(".")
    return FORMAT_REGISTRY.get(ext, FORMAT_REGISTRY.get("*"))


def get_processor_for_file(filepath: str, mime_type: str = None) -> tuple[ProcessorType, ExtractionStrategy]:
    """Bestimmt Processor und Strategy für eine Datei."""
    from pathlib import Path

    ext = Path(filepath).suffix.lower().lstrip(".")
    spec = get_format_spec(ext)

    # TODO: Magic Bytes prüfen für bessere Erkennung

    return spec.processor, spec.strategy


def get_all_supported_extensions() -> list[str]:
    """Gibt alle unterstützten Extensions zurück."""
    return [ext for ext in FORMAT_REGISTRY.keys() if ext != "*"]


def get_formats_by_category(category: str) -> list[FormatSpec]:
    """Gibt alle Formate einer Kategorie zurück."""
    return [spec for spec in FORMAT_REGISTRY.values() if spec.category == category]


def get_categories() -> list[str]:
    """Gibt alle Kategorien zurück."""
    return list(set(spec.category for spec in FORMAT_REGISTRY.values()))


def get_format_stats() -> dict:
    """Gibt Statistiken über die Format-Registry zurück."""
    categories = {}
    for spec in FORMAT_REGISTRY.values():
        if spec.extension == "*":
            continue
        cat = spec.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(spec.extension)

    return {
        "total_formats": len(FORMAT_REGISTRY) - 1,  # -1 für Fallback
        "categories": len(categories),
        "by_category": {k: len(v) for k, v in categories.items()},
        "formats_by_category": categories
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import json

    stats = get_format_stats()
    print(f"Neural Vault Format Registry")
    print(f"=" * 50)
    print(f"Unterstützte Formate: {stats['total_formats']}")
    print(f"Kategorien: {stats['categories']}")
    print()
    print("Formate pro Kategorie:")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
