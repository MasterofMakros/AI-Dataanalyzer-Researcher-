"""
Neural Vault Surya OCR Client
=============================

Client für den Surya OCR API Service mit:
- 97.7% Accuracy (vs. Tesseract 87%)
- Layout-Analyse
- Fallback auf Tesseract

Usage:
    from scripts.services.surya_client import SuryaClient

    client = SuryaClient()
    result = client.ocr("/path/to/image.png")

    # Mit Layout-Analyse
    result = client.ocr_with_layout("/path/to/invoice.pdf")
"""

import os
import sys
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

# Surya OCR API URL
SURYA_URL = os.getenv("SURYA_URL", "http://localhost:9999")

# Fallback: Tesseract
TESSERACT_AVAILABLE = False
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    pass

# Unterstützte Bild-Formate
IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".tiff", ".tif",
    ".bmp", ".webp", ".gif"
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BoundingBox:
    """Bounding Box für Text."""
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass
class TextLine:
    """Eine erkannte Textzeile."""
    text: str
    confidence: float
    bbox: Optional[BoundingBox] = None


@dataclass
class LayoutBlock:
    """Ein Layout-Block (Tabelle, Überschrift, etc.)."""
    block_type: str  # "text", "table", "figure", "header"
    bbox: BoundingBox
    lines: List[TextLine] = field(default_factory=list)


@dataclass
class OCRResult:
    """Vollständiges OCR-Ergebnis."""
    text: str
    lines: List[TextLine]
    layout: Optional[List[LayoutBlock]] = None
    language: str = "unknown"
    confidence: float = 0.0
    width: int = 0
    height: int = 0
    source: str = "surya"  # "surya" oder "tesseract"

    def get_text_by_region(
        self,
        x1: float, y1: float,
        x2: float, y2: float
    ) -> str:
        """Gibt Text in einer bestimmten Region zurück."""
        region_lines = []
        for line in self.lines:
            if line.bbox:
                # Prüfe Überlappung
                if (line.bbox.x1 < x2 and line.bbox.x2 > x1 and
                    line.bbox.y1 < y2 and line.bbox.y2 > y1):
                    region_lines.append(line.text)
        return "\n".join(region_lines)

    def get_tables(self) -> List[LayoutBlock]:
        """Gibt alle erkannten Tabellen zurück."""
        if not self.layout:
            return []
        return [b for b in self.layout if b.block_type == "table"]

    def to_searchable_text(self) -> str:
        """Generiert durchsuchbaren Text mit Struktur."""
        if not self.layout:
            return self.text

        sections = []
        for block in self.layout:
            if block.block_type == "header":
                sections.append(f"## {' '.join(l.text for l in block.lines)}")
            elif block.block_type == "table":
                sections.append("[TABLE]")
                for line in block.lines:
                    sections.append(f"  {line.text}")
                sections.append("[/TABLE]")
            else:
                for line in block.lines:
                    sections.append(line.text)

        return "\n".join(sections)


# =============================================================================
# CLIENT
# =============================================================================

class SuryaClient:
    """
    Client für Surya OCR API Service.

    Unterstützt automatischen Fallback auf Tesseract.
    """

    def __init__(
        self,
        surya_url: str = None,
        timeout: int = 120,
        default_langs: List[str] = None,
    ):
        """
        Initialisiert den Client.

        Args:
            surya_url: URL des Surya OCR Service
            timeout: Request Timeout in Sekunden
            default_langs: Standard-Sprachen (z.B. ["de", "en"])
        """
        self.surya_url = surya_url or SURYA_URL
        self.timeout = timeout
        self.default_langs = default_langs or ["de", "en"]
        self._use_surya = None  # Lazy detection

    @property
    def use_surya(self) -> bool:
        """Prüft ob Surya verfügbar ist."""
        # Feature Flag prüfen
        if not is_enabled("USE_SURYA_OCR"):
            return False

        # Lazy detection
        if self._use_surya is None:
            self._use_surya = self._check_surya_available()
        return self._use_surya

    def _check_surya_available(self) -> bool:
        """Prüft ob Surya Service erreichbar ist."""
        try:
            response = requests.get(
                f"{self.surya_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def ocr(
        self,
        image_path: str,
        langs: List[str] = None,
    ) -> OCRResult:
        """
        Führt OCR auf einem Bild durch.

        Args:
            image_path: Pfad zum Bild
            langs: Sprachen (z.B. ["de", "en"])

        Returns:
            OCRResult
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        langs = langs or self.default_langs

        # Surya oder Fallback
        if self.use_surya:
            return self._ocr_surya(image_path, langs, with_layout=False)
        else:
            return self._ocr_tesseract(image_path, langs)

    def ocr_with_layout(
        self,
        image_path: str,
        langs: List[str] = None,
    ) -> OCRResult:
        """
        OCR mit Layout-Analyse.

        Args:
            image_path: Pfad zum Bild
            langs: Sprachen

        Returns:
            OCRResult mit Layout-Blöcken
        """
        langs = langs or self.default_langs

        if self.use_surya:
            return self._ocr_surya(image_path, langs, with_layout=True)
        else:
            # Tesseract hat keine Layout-Analyse
            return self._ocr_tesseract(image_path, langs)

    def _ocr_surya(
        self,
        image_path: str,
        langs: List[str],
        with_layout: bool,
    ) -> OCRResult:
        """OCR via Surya API."""
        endpoint = "/ocr/layout" if with_layout else "/ocr"
        url = f"{self.surya_url}{endpoint}"

        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f)}
            params = {"langs": ",".join(langs)}

            response = requests.post(
                url,
                files=files,
                params=params,
                timeout=self.timeout
            )

        if response.status_code != 200:
            raise RuntimeError(f"Surya OCR error: {response.text}")

        data = response.json()
        return self._parse_surya_result(data)

    def _ocr_tesseract(
        self,
        image_path: str,
        langs: List[str],
    ) -> OCRResult:
        """Fallback: OCR via Tesseract."""
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract not available and Surya not reachable")

        from PIL import Image

        # Tesseract Sprach-Mapping
        lang_map = {
            "de": "deu",
            "en": "eng",
            "fr": "fra",
            "es": "spa",
            "it": "ita",
        }
        tess_langs = "+".join(lang_map.get(l, l) for l in langs)

        image = Image.open(image_path)

        # OCR mit Tesseract
        text = pytesseract.image_to_string(image, lang=tess_langs)

        # Detaillierte Daten
        data = pytesseract.image_to_data(image, lang=tess_langs, output_type=pytesseract.Output.DICT)

        lines = []
        current_line = []
        current_line_num = -1

        for i, word in enumerate(data["text"]):
            if not word.strip():
                continue

            line_num = data["line_num"][i]
            conf = float(data["conf"][i]) / 100

            if line_num != current_line_num and current_line:
                # Zeile abschließen
                line_text = " ".join(w["text"] for w in current_line)
                avg_conf = sum(w["conf"] for w in current_line) / len(current_line)
                lines.append(TextLine(
                    text=line_text,
                    confidence=avg_conf,
                    bbox=None,  # Tesseract gibt Box pro Wort, nicht pro Zeile
                ))
                current_line = []

            current_line_num = line_num
            current_line.append({"text": word, "conf": conf})

        # Letzte Zeile
        if current_line:
            line_text = " ".join(w["text"] for w in current_line)
            avg_conf = sum(w["conf"] for w in current_line) / len(current_line)
            lines.append(TextLine(text=line_text, confidence=avg_conf))

        avg_confidence = sum(l.confidence for l in lines) / len(lines) if lines else 0

        return OCRResult(
            text=text.strip(),
            lines=lines,
            layout=None,
            language=langs[0] if langs else "unknown",
            confidence=avg_confidence,
            width=image.width,
            height=image.height,
            source="tesseract",
        )

    def _parse_surya_result(self, data: dict) -> OCRResult:
        """Parsed Surya API Antwort."""
        lines = []
        for line_data in data.get("lines", []):
            bbox = None
            if "bbox" in line_data:
                b = line_data["bbox"]
                bbox = BoundingBox(
                    x1=b.get("x1", 0),
                    y1=b.get("y1", 0),
                    x2=b.get("x2", 0),
                    y2=b.get("y2", 0),
                )

            lines.append(TextLine(
                text=line_data.get("text", ""),
                confidence=line_data.get("confidence", 0),
                bbox=bbox,
            ))

        # Layout-Blöcke
        layout = None
        if "layout" in data and data["layout"]:
            layout = []
            for block_data in data["layout"]:
                b = block_data.get("bbox", {})
                bbox = BoundingBox(
                    x1=b.get("x1", 0),
                    y1=b.get("y1", 0),
                    x2=b.get("x2", 0),
                    y2=b.get("y2", 0),
                )
                layout.append(LayoutBlock(
                    block_type=block_data.get("type", "text"),
                    bbox=bbox,
                    lines=[],
                ))

        return OCRResult(
            text=data.get("text", ""),
            lines=lines,
            layout=layout,
            language=data.get("language", "unknown"),
            confidence=data.get("confidence", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            source="surya",
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Singleton Client
_client: Optional[SuryaClient] = None


def get_client() -> SuryaClient:
    """Holt den Default-Client."""
    global _client
    if _client is None:
        _client = SuryaClient()
    return _client


def ocr(image_path: str, langs: List[str] = None) -> OCRResult:
    """
    Convenience-Funktion für OCR.

    Args:
        image_path: Pfad zum Bild
        langs: Sprachen

    Returns:
        OCRResult
    """
    return get_client().ocr(image_path, langs)


def is_image_file(filepath: Path) -> bool:
    """Prüft ob Datei ein Bild-Format ist."""
    return filepath.suffix.lower() in IMAGE_EXTENSIONS


# =============================================================================
# MAIN (Test)
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python surya_client.py <image_file>")
        sys.exit(1)

    image_path = sys.argv[1]
    print(f"OCR: {image_path}")

    client = SuryaClient()
    print(f"Using Surya: {client.use_surya}")

    try:
        result = client.ocr_with_layout(image_path)

        print(f"\nLanguage: {result.language}")
        print(f"Confidence: {result.confidence:.2%}")
        print(f"Lines: {len(result.lines)}")
        print(f"Source: {result.source}")

        if result.layout:
            print(f"Layout Blocks: {len(result.layout)}")
            for block in result.layout:
                print(f"  - {block.block_type}: {block.bbox.width:.0f}x{block.bbox.height:.0f}")

        print(f"\n--- Text ---")
        print(result.text[:1000])

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
