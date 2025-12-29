"""
Neural Vault Unified Extraction Service
========================================

Docling-First Strategie mit Fallback Chains.

Benchmark-Basis:
- Docling: 97.9% Table Accuracy
- Tika: 75% Table Accuracy
- Surya OCR: 97.7% vs Tesseract 87%

Usage:
    from scripts.services.extraction_service import extract_text, ExtractionResult

    result = extract_text("/path/to/document.pdf")
    print(result.text)
    print(f"Extracted via: {result.source}")
"""

import os
import sys
import requests
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Projekt-Root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.parser_routing import (
    get_parser, get_fallback_chain, get_parser_config,
    ParserType, ParserConfig, PARSER_CONFIGS
)
from config.feature_flags import is_enabled


# =============================================================================
# CONFIGURATION
# =============================================================================

# Service URLs (überschreibbar via Environment)
# document-processor ist der unified service (Docling + Surya + GLiNER)
DOCUMENT_PROCESSOR_URL = os.getenv("DOCUMENT_PROCESSOR_URL", "http://localhost:8005")
DOCLING_URL = os.getenv("DOCLING_URL", DOCUMENT_PROCESSOR_URL)  # Backward compat
TIKA_URL = os.getenv("TIKA_URL", "http://localhost:9998")
SURYA_URL = os.getenv("SURYA_URL", DOCUMENT_PROCESSOR_URL)  # Unified service
WHISPERX_URL = os.getenv("WHISPERX_URL", "http://localhost:9000")


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ExtractionResult:
    """Ergebnis einer Text-Extraktion."""
    text: str
    source: str  # "docling", "tika", "surya", "whisperx"
    success: bool = True
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    fallback_used: bool = False
    original_error: Optional[str] = None

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def line_count(self) -> int:
        return len(self.text.splitlines()) if self.text else 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "success": self.success,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "fallback_used": self.fallback_used,
            "char_count": self.char_count,
            "line_count": self.line_count,
        }


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def _extract_docling(filepath: Path, timeout: int = 180) -> ExtractionResult:
    """
    Extraktion via Docling (Neural Worker).

    Docling bietet:
    - 97.9% Table Accuracy (vs. Tika 75%)
    - Strukturerhalt (Markdown)
    - Layout-Analyse
    """
    try:
        with open(filepath, "rb") as f:
            files = {"file": (filepath.name, f)}

            response = requests.post(
                f"{DOCLING_URL}/process/document",
                files=files,
                timeout=timeout
            )

        if response.status_code != 200:
            return ExtractionResult(
                text="",
                source="docling",
                success=False,
                original_error=f"HTTP {response.status_code}: {response.text[:200]}"
            )

        data = response.json()

        return ExtractionResult(
            text=data.get("markdown", data.get("text", "")),
            source="docling",
            success=True,
            confidence=data.get("confidence", 0.95),
            metadata={
                "tables_found": data.get("tables_count", 0),
                "pages": data.get("pages", 0),
                "layout_blocks": data.get("layout_blocks", []),
            }
        )

    except requests.exceptions.ConnectionError:
        return ExtractionResult(
            text="",
            source="docling",
            success=False,
            original_error="Docling service not available"
        )
    except Exception as e:
        return ExtractionResult(
            text="",
            source="docling",
            success=False,
            original_error=str(e)
        )


def _extract_tika(filepath: Path, prefer_markdown: bool = True, timeout: int = 60) -> ExtractionResult:
    """
    Extraktion via Apache Tika.

    Tika bietet:
    - 1400+ Formate
    - Stabil und bewährt
    - Schnell
    """
    try:
        with open(filepath, "rb") as f:
            # HTML für bessere Tabellenerhaltung
            accept = "text/html" if prefer_markdown else "text/plain"

            response = requests.put(
                f"{TIKA_URL}/tika",
                data=f,
                headers={"Accept": accept},
                timeout=timeout
            )

        if response.status_code != 200:
            return ExtractionResult(
                text="",
                source="tika",
                success=False,
                original_error=f"HTTP {response.status_code}"
            )

        text = response.text.strip()

        # HTML zu Markdown konvertieren
        if prefer_markdown and "<" in text:
            try:
                import html2text
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = True
                h.body_width = 0
                text = h.handle(text)
            except ImportError:
                pass

        return ExtractionResult(
            text=text,
            source="tika",
            success=True,
            confidence=0.75,  # Tika Baseline
        )

    except requests.exceptions.ConnectionError:
        return ExtractionResult(
            text="",
            source="tika",
            success=False,
            original_error="Tika service not available"
        )
    except Exception as e:
        return ExtractionResult(
            text="",
            source="tika",
            success=False,
            original_error=str(e)
        )


def _extract_surya(filepath: Path, langs: List[str] = None, timeout: int = 120) -> ExtractionResult:
    """
    OCR via Surya (97.7% Accuracy).

    Surya bietet:
    - 97.7% Accuracy (vs. Tesseract 87%)
    - Layout-Analyse
    - 90+ Sprachen

    Nutzt den unified document-processor Service.
    """
    langs = langs or ["de", "en"]

    try:
        with open(filepath, "rb") as f:
            files = {"file": (filepath.name, f)}
            params = {"processor": "surya", "langs": ",".join(langs)}

            # Unified endpoint: /process/document oder /process/ocr
            response = requests.post(
                f"{SURYA_URL}/process/ocr",
                files=files,
                params=params,
                timeout=timeout
            )

        if response.status_code != 200:
            return ExtractionResult(
                text="",
                source="surya",
                success=False,
                original_error=f"HTTP {response.status_code}"
            )

        data = response.json()

        return ExtractionResult(
            text=data.get("text", ""),
            source="surya",
            success=True,
            confidence=data.get("confidence", 0.97),
            metadata={
                "lines": len(data.get("lines", [])),
                "layout_blocks": len(data.get("layout", []) or []),
                "language": data.get("language", "unknown"),
            }
        )

    except requests.exceptions.ConnectionError:
        # Fallback auf Tesseract via surya_client
        try:
            from scripts.services.surya_client import SuryaClient
            client = SuryaClient()
            result = client.ocr_with_layout(str(filepath), langs)

            return ExtractionResult(
                text=result.text,
                source=result.source,  # "surya" oder "tesseract"
                success=True,
                confidence=result.confidence,
                fallback_used=(result.source == "tesseract"),
                metadata={
                    "lines": len(result.lines),
                    "language": result.language,
                }
            )
        except Exception as e:
            return ExtractionResult(
                text="",
                source="surya",
                success=False,
                original_error=f"Surya and Tesseract fallback failed: {e}"
            )
    except Exception as e:
        return ExtractionResult(
            text="",
            source="surya",
            success=False,
            original_error=str(e)
        )


def _extract_whisperx(filepath: Path, language: str = None, timeout: int = 600) -> ExtractionResult:
    """
    Audio/Video Transcription via WhisperX.

    WhisperX bietet:
    - Word-Level Timestamps
    - Speaker Diarization
    - 70x Realtime Speed
    """
    try:
        with open(filepath, "rb") as f:
            files = {"file": (filepath.name, f)}
            data = {}
            if language:
                data["language"] = language

            response = requests.post(
                f"{WHISPERX_URL}/transcribe",
                files=files,
                data=data,
                timeout=timeout
            )

        if response.status_code != 200:
            return ExtractionResult(
                text="",
                source="whisperx",
                success=False,
                original_error=f"HTTP {response.status_code}"
            )

        result = response.json()

        # Text mit Timestamps formatieren
        text_parts = []
        for segment in result.get("segments", []):
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            text = segment.get("text", "")
            speaker = segment.get("speaker", "")

            # Format: [MM:SS-MM:SS] (Speaker) Text
            start_fmt = f"{int(start//60):02d}:{int(start%60):02d}"
            end_fmt = f"{int(end//60):02d}:{int(end%60):02d}"

            if speaker:
                text_parts.append(f"[{start_fmt}-{end_fmt}] ({speaker}) {text}")
            else:
                text_parts.append(f"[{start_fmt}-{end_fmt}] {text}")

        full_text = "\n".join(text_parts) if text_parts else result.get("text", "")

        return ExtractionResult(
            text=full_text,
            source="whisperx",
            success=True,
            confidence=0.95,
            metadata={
                "language": result.get("language", "unknown"),
                "duration": result.get("duration", 0),
                "segments": len(result.get("segments", [])),
                "speakers": result.get("speakers", []),
            }
        )

    except requests.exceptions.ConnectionError:
        # Fallback auf whisperx_client
        try:
            from scripts.services.whisperx_client import WhisperXClient
            client = WhisperXClient()
            result = client.transcribe(str(filepath), language)

            return ExtractionResult(
                text=result.to_searchable_text(),
                source=result.source,
                success=True,
                confidence=0.95,
                fallback_used=(result.source == "faster-whisper"),
                metadata={
                    "language": result.language,
                    "duration": result.duration,
                    "segments": len(result.segments),
                }
            )
        except Exception as e:
            return ExtractionResult(
                text="",
                source="whisperx",
                success=False,
                original_error=f"WhisperX and fallback failed: {e}"
            )
    except Exception as e:
        return ExtractionResult(
            text="",
            source="whisperx",
            success=False,
            original_error=str(e)
        )


def _extract_archive(filepath: Path) -> ExtractionResult:
    """
    Archiv-Extraktion (ZIP, RAR, 7z, etc.).

    Extrahiert nur Metadaten und Dateiliste.
    Die eigentliche Verarbeitung erfolgt separat.
    """
    import zipfile
    import tarfile

    ext = filepath.suffix.lower()
    file_list = []

    try:
        if ext == ".zip":
            with zipfile.ZipFile(filepath, 'r') as zf:
                file_list = zf.namelist()
        elif ext in {".tar", ".gz", ".tgz"}:
            with tarfile.open(filepath, 'r:*') as tf:
                file_list = tf.getnames()
        else:
            # 7z, RAR - benötigen externe Tools
            return ExtractionResult(
                text=f"[Archive: {filepath.name}]\nFormat: {ext}\nExtraction requires external tools.",
                source="archive",
                success=True,
                metadata={"format": ext}
            )

        text = f"[Archive: {filepath.name}]\n"
        text += f"Files: {len(file_list)}\n\n"
        text += "\n".join(file_list[:100])  # Max 100 Dateien auflisten
        if len(file_list) > 100:
            text += f"\n... and {len(file_list) - 100} more files"

        return ExtractionResult(
            text=text,
            source="archive",
            success=True,
            metadata={
                "file_count": len(file_list),
                "files": file_list[:100],
            }
        )

    except Exception as e:
        return ExtractionResult(
            text="",
            source="archive",
            success=False,
            original_error=str(e)
        )


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================

def extract_text(
    filepath: str | Path,
    force_parser: ParserType = None,
    use_fallback: bool = True,
    langs: List[str] = None,
) -> ExtractionResult:
    """
    Extrahiert Text aus einer Datei mit Docling-First Strategie.

    Die Strategie basiert auf Benchmarks:
    - Docling: 97.9% Table Accuracy für strukturierte Dokumente
    - Surya: 97.7% OCR Accuracy für Bilder
    - WhisperX: Word-Level Timestamps für Audio
    - Tika: Universal Fallback für 1400+ Formate

    Args:
        filepath: Pfad zur Datei
        force_parser: Parser erzwingen (überschreibt Routing)
        use_fallback: Fallback Chain nutzen wenn primärer Parser fehlschlägt
        langs: Sprachen für OCR/Transcription

    Returns:
        ExtractionResult mit Text, Source und Metadaten
    """
    path = Path(filepath)

    if not path.exists():
        return ExtractionResult(
            text="",
            source="none",
            success=False,
            original_error=f"File not found: {filepath}"
        )

    ext = path.suffix.lower()

    # Feature Flag Check
    if not is_enabled("USE_PARSER_ROUTING"):
        # Legacy: Nur Tika
        return _extract_tika(path)

    # Parser bestimmen
    if force_parser:
        parser_chain = [force_parser]
    else:
        parser_chain = get_fallback_chain(ext) if use_fallback else [get_parser(ext)]

    # Extraction Dispatcher
    extractors = {
        ParserType.DOCLING: lambda: _extract_docling(path),
        ParserType.TIKA: lambda: _extract_tika(path),
        ParserType.SURYA: lambda: _extract_surya(path, langs),
        ParserType.WHISPERX: lambda: _extract_whisperx(path),
        ParserType.ARCHIVE: lambda: _extract_archive(path),
    }

    # Fallback Chain durchlaufen
    last_result = None
    for i, parser in enumerate(parser_chain):
        extractor = extractors.get(parser)
        if not extractor:
            continue

        result = extractor()

        if result.success and result.text:
            # Markiere wenn Fallback verwendet wurde
            if i > 0:
                result.fallback_used = True
                result.metadata["original_parser"] = parser_chain[0].value
                result.metadata["fallback_reason"] = last_result.original_error if last_result else "unknown"

            return result

        last_result = result

    # Alle Parser fehlgeschlagen
    return ExtractionResult(
        text="",
        source=parser_chain[0].value if parser_chain else "none",
        success=False,
        original_error=last_result.original_error if last_result else "No parser available"
    )


def get_extraction_stats() -> Dict[str, Any]:
    """
    Gibt Statistiken über verfügbare Extraktoren zurück.
    """
    services = {}

    # Docling Check
    try:
        r = requests.get(f"{DOCLING_URL}/health", timeout=2)
        services["docling"] = r.status_code == 200
    except:
        services["docling"] = False

    # Tika Check
    try:
        r = requests.get(f"{TIKA_URL}/tika", timeout=2)
        services["tika"] = r.status_code in (200, 204, 405)
    except:
        services["tika"] = False

    # Surya Check
    try:
        r = requests.get(f"{SURYA_URL}/health", timeout=2)
        services["surya"] = r.status_code == 200
    except:
        services["surya"] = False

    # WhisperX Check
    try:
        r = requests.get(f"{WHISPERX_URL}/health", timeout=2)
        services["whisperx"] = r.status_code == 200
    except:
        services["whisperx"] = False

    return {
        "services": services,
        "docling_first_enabled": is_enabled("USE_PARSER_ROUTING"),
        "feature_flags": {
            "USE_PARSER_ROUTING": is_enabled("USE_PARSER_ROUTING"),
            "USE_DOCLING_FIRST": is_enabled("USE_DOCLING_FIRST"),
            "USE_SURYA_OCR": is_enabled("USE_SURYA_OCR"),
            "USE_WHISPERX": is_enabled("USE_WHISPERX"),
        }
    }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def extract_pdf(filepath: str | Path) -> ExtractionResult:
    """Extrahiert Text aus PDF (Docling-First)."""
    return extract_text(filepath, force_parser=ParserType.DOCLING)


def extract_image(filepath: str | Path, langs: List[str] = None) -> ExtractionResult:
    """OCR auf Bild (Surya-First)."""
    return extract_text(filepath, force_parser=ParserType.SURYA, langs=langs)


def extract_audio(filepath: str | Path, language: str = None) -> ExtractionResult:
    """Transcription von Audio (WhisperX)."""
    return extract_text(filepath, force_parser=ParserType.WHISPERX, langs=[language] if language else None)


# =============================================================================
# MAIN (Test)
# =============================================================================

if __name__ == "__main__":
    import sys

    print("Neural Vault Extraction Service")
    print("=" * 40)

    # Status anzeigen
    stats = get_extraction_stats()
    print("\nService Status:")
    for service, available in stats["services"].items():
        icon = "✅" if available else "❌"
        print(f"  {icon} {service}")

    print("\nFeature Flags:")
    for flag, enabled in stats["feature_flags"].items():
        icon = "✅" if enabled else "⬜"
        print(f"  {icon} {flag}")

    # Test-Extraktion
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        print(f"\n\nExtracting: {filepath}")
        print("-" * 40)

        result = extract_text(filepath)

        print(f"Source: {result.source}")
        print(f"Success: {result.success}")
        print(f"Fallback used: {result.fallback_used}")
        print(f"Confidence: {result.confidence:.1%}")
        print(f"Characters: {result.char_count}")
        print(f"Lines: {result.line_count}")

        if result.metadata:
            print(f"Metadata: {result.metadata}")

        if result.original_error:
            print(f"Error: {result.original_error}")

        print(f"\n--- Text (first 500 chars) ---")
        print(result.text[:500])
