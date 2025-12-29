"""
Neural Vault Tika Markdown Extractor
====================================

Extrahiert Inhalte via Apache Tika im HTML-Format und konvertiert
zu Markdown, um Struktur (Tabellen, Überschriften) zu erhalten.

Übernahme aus Gemini-Analyse vom 2025-12-28:
"Wir konfigurieren Tika so, dass es HTML/XHTML liefert, nicht Plaintext.
HTML-to-Markdown konvertieren (erhält Tabellenstrukturen!)."

Usage:
    from utils.tika_markdown import extract_markdown, TikaExtractor

    # Einfache Nutzung
    md_text = extract_markdown("/path/to/document.pdf")

    # Mit mehr Kontrolle
    extractor = TikaExtractor()
    result = extractor.extract(path, include_metadata=True)
"""

import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import re
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from config.paths import TIKA_URL
except ImportError:
    TIKA_URL = "http://localhost:9998/tika"

# Optionale Abhängigkeit: markdownify für bessere HTML→MD Konvertierung
try:
    from markdownify import markdownify as md
    MARKDOWNIFY_AVAILABLE = True
except ImportError:
    MARKDOWNIFY_AVAILABLE = False
    print("[WARN] markdownify nicht installiert, nutze Fallback-Konvertierung")


@dataclass
class TikaResult:
    """Ergebnis einer Tika-Extraktion."""
    text: str                          # Extrahierter Text (Markdown oder Plain)
    html: Optional[str] = None         # Original HTML (falls angefordert)
    metadata: Optional[Dict] = None    # Tika Metadaten
    format: str = "markdown"           # "markdown" oder "plain"
    success: bool = True
    error: Optional[str] = None


class TikaExtractor:
    """
    Extrahiert Dokumenteninhalte via Apache Tika.

    Unterstützt zwei Modi:
    1. HTML → Markdown (strukturerhaltend, für Tabellen)
    2. Plain Text (schneller, für einfache Texte)
    """

    def __init__(self, tika_url: Optional[str] = None, timeout: int = 120):
        self.tika_url = tika_url or TIKA_URL
        self.timeout = timeout

    def extract(
        self,
        filepath: Path,
        prefer_markdown: bool = True,
        include_metadata: bool = False,
        include_html: bool = False
    ) -> TikaResult:
        """
        Extrahiert Text aus einer Datei via Tika.

        Args:
            filepath: Pfad zur Datei
            prefer_markdown: HTML holen und zu Markdown konvertieren
            include_metadata: Tika-Metadaten einschließen
            include_html: Original-HTML behalten

        Returns:
            TikaResult mit extrahiertem Text
        """
        filepath = Path(filepath)

        if not filepath.exists():
            return TikaResult(
                text="",
                success=False,
                error=f"Datei nicht gefunden: {filepath}"
            )

        try:
            # Metadaten abrufen (optional)
            metadata = None
            if include_metadata:
                metadata = self._get_metadata(filepath)

            # Inhalt extrahieren
            if prefer_markdown:
                html = self._extract_html(filepath)
                if html:
                    text = self._html_to_markdown(html)
                    return TikaResult(
                        text=text,
                        html=html if include_html else None,
                        metadata=metadata,
                        format="markdown",
                        success=True
                    )
                else:
                    # Fallback zu Plain Text
                    text = self._extract_plain(filepath)
                    return TikaResult(
                        text=text or "",
                        metadata=metadata,
                        format="plain",
                        success=bool(text)
                    )
            else:
                text = self._extract_plain(filepath)
                return TikaResult(
                    text=text or "",
                    metadata=metadata,
                    format="plain",
                    success=bool(text)
                )

        except Exception as e:
            return TikaResult(
                text="",
                success=False,
                error=str(e)
            )

    def _extract_html(self, filepath: Path) -> Optional[str]:
        """Extrahiert HTML via Tika."""
        try:
            with open(filepath, "rb") as f:
                response = requests.put(
                    self.tika_url,
                    data=f,
                    headers={"Accept": "text/html"},
                    timeout=self.timeout
                )
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"  ⚠️ Tika HTML Fehler: {e}")
        return None

    def _extract_plain(self, filepath: Path) -> Optional[str]:
        """Extrahiert Plain Text via Tika."""
        try:
            with open(filepath, "rb") as f:
                response = requests.put(
                    self.tika_url,
                    data=f,
                    headers={"Accept": "text/plain"},
                    timeout=self.timeout
                )
            if response.status_code == 200:
                return response.text.strip()
        except Exception as e:
            print(f"  ⚠️ Tika Plain Fehler: {e}")
        return None

    def _get_metadata(self, filepath: Path) -> Optional[Dict]:
        """Holt Metadaten via Tika."""
        try:
            with open(filepath, "rb") as f:
                response = requests.put(
                    f"{self.tika_url.replace('/tika', '/meta')}",
                    data=f,
                    headers={"Accept": "application/json"},
                    timeout=30
                )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"  ⚠️ Tika Metadata Fehler: {e}")
        return None

    def _html_to_markdown(self, html: str) -> str:
        """Konvertiert HTML zu Markdown."""
        if MARKDOWNIFY_AVAILABLE:
            return self._convert_with_markdownify(html)
        else:
            return self._convert_fallback(html)

    def _convert_with_markdownify(self, html: str) -> str:
        """Konvertiert HTML zu Markdown mit markdownify."""
        try:
            # Optionen für bessere Konvertierung
            markdown = md(
                html,
                heading_style="ATX",           # # Heading statt underline
                bullets="-",                   # - statt *
                strip=["script", "style"],     # JS/CSS entfernen
                convert=["table", "tr", "td", "th", "p", "h1", "h2", "h3", "h4", "ul", "ol", "li", "a", "strong", "em"]
            )

            # Aufräumen
            markdown = self._cleanup_markdown(markdown)
            return markdown

        except Exception as e:
            print(f"  ⚠️ markdownify Fehler: {e}, nutze Fallback")
            return self._convert_fallback(html)

    def _convert_fallback(self, html: str) -> str:
        """Einfache HTML → Text Konvertierung ohne Bibliothek."""
        import html as html_module

        # Tags entfernen
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Überschriften
        text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', text, flags=re.IGNORECASE)

        # Listen
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', text, flags=re.IGNORECASE | re.DOTALL)

        # Paragraphen
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

        # Tabellen (vereinfacht)
        text = re.sub(r'<tr[^>]*>', '| ', text, flags=re.IGNORECASE)
        text = re.sub(r'</tr>', ' |\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<t[dh][^>]*>(.*?)</t[dh]>', r'\1 | ', text, flags=re.IGNORECASE | re.DOTALL)

        # Alle restlichen Tags entfernen
        text = re.sub(r'<[^>]+>', '', text)

        # HTML-Entities dekodieren
        text = html_module.unescape(text)

        return self._cleanup_markdown(text)

    def _cleanup_markdown(self, text: str) -> str:
        """Bereinigt Markdown-Text."""
        # Mehrfache Leerzeilen reduzieren
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Führende/trailing Whitespace pro Zeile
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # Mehrfache Leerzeichen
        text = re.sub(r' {2,}', ' ', text)

        return text.strip()


def extract_markdown(
    filepath: str | Path,
    tika_url: Optional[str] = None
) -> str:
    """
    Convenience-Funktion: Extrahiert Markdown aus einer Datei.

    Args:
        filepath: Pfad zur Datei
        tika_url: Optionale Tika-URL

    Returns:
        Extrahierter Text als Markdown
    """
    extractor = TikaExtractor(tika_url=tika_url)
    result = extractor.extract(Path(filepath), prefer_markdown=True)
    return result.text


def extract_with_metadata(
    filepath: str | Path,
    tika_url: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Extrahiert Markdown und Metadaten aus einer Datei.

    Returns:
        Tuple aus (markdown_text, metadata_dict)
    """
    extractor = TikaExtractor(tika_url=tika_url)
    result = extractor.extract(
        Path(filepath),
        prefer_markdown=True,
        include_metadata=True
    )
    return result.text, result.metadata or {}


# Beispiel-Nutzung
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python tika_markdown.py <filepath>")
        print("\nBeispiel:")
        print("  python tika_markdown.py /path/to/document.pdf")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"❌ Datei nicht gefunden: {filepath}")
        sys.exit(1)

    print(f"📄 Extrahiere: {filepath}")
    print("-" * 50)

    extractor = TikaExtractor()
    result = extractor.extract(filepath, include_metadata=True)

    if result.success:
        print(f"✅ Format: {result.format}")
        print(f"📏 Länge: {len(result.text)} Zeichen")
        print()

        if result.metadata:
            print("📋 Metadaten:")
            for key, value in list(result.metadata.items())[:10]:
                print(f"   {key}: {value}")
            print()

        print("📝 Inhalt (erste 1000 Zeichen):")
        print("-" * 50)
        print(result.text[:1000])
        if len(result.text) > 1000:
            print(f"\n... ({len(result.text) - 1000} weitere Zeichen)")
    else:
        print(f"❌ Fehler: {result.error}")
