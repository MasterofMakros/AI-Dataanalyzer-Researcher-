"""
Neural Vault API Service
========================

Zentraler API-Endpunkt für alle Neural Vault Operationen.
Läuft als Docker-Container und verbindet alle Services.

Endpoints:
- /health - Health Check
- /search - Meilisearch Suche mit Context Headers
- /feedback - User-Korrektur Tracking
- /extract - Tika HTML→Markdown Extraktion
- /index - Meilisearch Index-Operationen
- /stats - Statistiken und Metriken
"""

import os
import json
import hashlib
import sqlite3
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import requests
import httpx
from fastapi import FastAPI, HTTPException, Query, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import redis

# Optionale Abhängigkeit
try:
    from markdownify import markdownify as md
    MARKDOWNIFY_AVAILABLE = True
except ImportError:
    MARKDOWNIFY_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================

# Service URLs (Docker internal network)
MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://meilisearch:7700")
MEILISEARCH_KEY = os.getenv("MEILI_MASTER_KEY", "")
TIKA_URL = os.getenv("TIKA_URL", "http://tika:9998/tika")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")

# Data paths (mounted volumes)
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
FEEDBACK_DB_PATH = DATA_DIR / "feedback_tracker.db"

# Index configuration
INDEX_NAME = "files"


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    filters: Optional[str] = None
    sort: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    attributes_to_retrieve: Optional[List[str]] = None


class SearchResult(BaseModel):
    hits: List[Dict[str, Any]]
    total: int
    processing_time_ms: int
    query: str


class FeedbackRequest(BaseModel):
    file_hash: str
    filename: str
    predicted_category: str
    actual_category: str
    predicted_path: Optional[str] = None
    actual_path: Optional[str] = None
    predicted_confidence: Optional[float] = None
    user_comment: Optional[str] = None


class FeedbackStats(BaseModel):
    total_corrections: int
    by_type: Dict[str, int]
    top_misclassifications: List[Dict[str, Any]]
    corrections_by_week: Dict[str, int]


class ExtractRequest(BaseModel):
    file_path: str
    prefer_markdown: bool = True
    include_metadata: bool = False


class ExtractResult(BaseModel):
    text: str
    format: str
    metadata: Optional[Dict[str, Any]] = None
    success: bool
    error: Optional[str] = None


class IndexDocumentRequest(BaseModel):
    documents: List[Dict[str, Any]]


class HealthStatus(BaseModel):
    status: str
    services: Dict[str, bool]
    timestamp: str


# =============================================================================
# SOURCE TYPE & CONTEXT HEADERS
# =============================================================================

class SourceType(str, Enum):
    PDF_DOCUMENT = "pdf_document"
    SPREADSHEET = "spreadsheet"
    EMAIL = "email"
    IMAGE_OCR = "image_ocr"
    AUDIO_TRANSCRIPT = "audio_transcript"
    VIDEO_TRANSCRIPT = "video_transcript"
    TEXT_FILE = "text_file"
    CODE_FILE = "code_file"
    ARCHIVE_LISTING = "archive_listing"
    UNKNOWN = "unknown"


@dataclass
class ChunkLocation:
    page: Optional[int] = None
    total_pages: Optional[int] = None
    sheet_name: Optional[str] = None
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None


def format_timestamp(seconds: float) -> str:
    """Formatiert Sekunden als HH:MM:SS oder MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def detect_source_type(mime_type: Optional[str] = None, extension: Optional[str] = None) -> SourceType:
    """Erkennt den Quelltyp basierend auf MIME-Type oder Extension."""
    if mime_type:
        mime_lower = mime_type.lower()
        if "pdf" in mime_lower:
            return SourceType.PDF_DOCUMENT
        elif "spreadsheet" in mime_lower or "excel" in mime_lower:
            return SourceType.SPREADSHEET
        elif "email" in mime_lower or "message" in mime_lower:
            return SourceType.EMAIL
        elif mime_lower.startswith("image/"):
            return SourceType.IMAGE_OCR
        elif mime_lower.startswith("audio/"):
            return SourceType.AUDIO_TRANSCRIPT
        elif mime_lower.startswith("video/"):
            return SourceType.VIDEO_TRANSCRIPT
        elif mime_lower.startswith("text/"):
            return SourceType.TEXT_FILE

    if extension:
        ext = extension.lower().lstrip(".")
        ext_map = {
            "pdf": SourceType.PDF_DOCUMENT,
            "xlsx": SourceType.SPREADSHEET, "xls": SourceType.SPREADSHEET,
            "csv": SourceType.SPREADSHEET,
            "eml": SourceType.EMAIL, "msg": SourceType.EMAIL,
            "jpg": SourceType.IMAGE_OCR, "jpeg": SourceType.IMAGE_OCR,
            "png": SourceType.IMAGE_OCR, "tiff": SourceType.IMAGE_OCR,
            "mp3": SourceType.AUDIO_TRANSCRIPT, "wav": SourceType.AUDIO_TRANSCRIPT,
            "m4a": SourceType.AUDIO_TRANSCRIPT, "flac": SourceType.AUDIO_TRANSCRIPT,
            "mp4": SourceType.VIDEO_TRANSCRIPT, "mkv": SourceType.VIDEO_TRANSCRIPT,
            "avi": SourceType.VIDEO_TRANSCRIPT, "mov": SourceType.VIDEO_TRANSCRIPT,
            "py": SourceType.CODE_FILE, "js": SourceType.CODE_FILE,
            "ts": SourceType.CODE_FILE, "java": SourceType.CODE_FILE,
            "zip": SourceType.ARCHIVE_LISTING, "rar": SourceType.ARCHIVE_LISTING,
            "7z": SourceType.ARCHIVE_LISTING, "tar": SourceType.ARCHIVE_LISTING,
        }
        return ext_map.get(ext, SourceType.TEXT_FILE)

    return SourceType.UNKNOWN


def wrap_chunk(
    text: str,
    source_type: SourceType,
    filename: str,
    location: Optional[ChunkLocation] = None,
    confidence: Optional[float] = None,
    category: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Fügt strukturierten Context Header zu einem Text-Chunk hinzu."""
    header_parts = [f"SOURCE: {filename}", f"TYPE: {source_type.value}"]

    if location:
        if location.page is not None:
            page_info = f"PAGE: {location.page}"
            if location.total_pages:
                page_info += f"/{location.total_pages}"
            header_parts.append(page_info)

        if location.sheet_name:
            header_parts.append(f"SHEET: {location.sheet_name}")

        if location.timestamp_start is not None:
            ts_info = f"TIME: {format_timestamp(location.timestamp_start)}"
            if location.timestamp_end is not None:
                ts_info += f"-{format_timestamp(location.timestamp_end)}"
            header_parts.append(ts_info)

        if location.line_start is not None:
            line_info = f"LINES: {location.line_start}"
            if location.line_end is not None:
                line_info += f"-{location.line_end}"
            header_parts.append(line_info)

    header_line_1 = f"[{' | '.join(header_parts)}]"

    meta_parts = []
    if category:
        meta_parts.append(f"CATEGORY: {category}")
    if confidence is not None:
        meta_parts.append(f"CONFIDENCE: {confidence:.2f}")
    if extra_metadata:
        for key, value in extra_metadata.items():
            if value is not None:
                meta_parts.append(f"{key.upper()}: {value}")

    if meta_parts:
        header_line_2 = f"[{' | '.join(meta_parts)}]"
        return f"{header_line_1}\n{header_line_2}\n---\n{text}"

    return f"{header_line_1}\n---\n{text}"


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
    """Convenience-Funktion für RAG-Chunks."""
    source_type = detect_source_type(mime_type=mime_type, extension=Path(filename).suffix)

    location = None
    if any([page, timestamp_start, sheet_name]):
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


# =============================================================================
# TIKA EXTRACTOR
# =============================================================================

class TikaExtractor:
    """Extrahiert Dokumenteninhalte via Apache Tika."""

    def __init__(self, tika_url: str = None, timeout: int = 120):
        self.tika_url = tika_url or TIKA_URL
        self.timeout = timeout

    def extract(
        self,
        filepath: Path,
        prefer_markdown: bool = True,
        include_metadata: bool = False,
        include_html: bool = False
    ) -> Dict[str, Any]:
        """Extrahiert Text aus einer Datei via Tika."""
        filepath = Path(filepath)

        if not filepath.exists():
            return {
                "text": "",
                "success": False,
                "error": f"Datei nicht gefunden: {filepath}",
                "format": "error"
            }

        try:
            metadata = None
            if include_metadata:
                metadata = self._get_metadata(filepath)

            if prefer_markdown:
                html = self._extract_html(filepath)
                if html:
                    text = self._html_to_markdown(html)
                    return {
                        "text": text,
                        "html": html if include_html else None,
                        "metadata": metadata,
                        "format": "markdown",
                        "success": True
                    }

            text = self._extract_plain(filepath)
            return {
                "text": text or "",
                "metadata": metadata,
                "format": "plain",
                "success": bool(text)
            }

        except Exception as e:
            return {
                "text": "",
                "success": False,
                "error": str(e),
                "format": "error"
            }

    def _extract_html(self, filepath: Path) -> Optional[str]:
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
        except Exception:
            pass
        return None

    def _extract_plain(self, filepath: Path) -> Optional[str]:
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
        except Exception:
            pass
        return None

    def _get_metadata(self, filepath: Path) -> Optional[Dict]:
        try:
            meta_url = self.tika_url.replace("/tika", "/meta")
            with open(filepath, "rb") as f:
                response = requests.put(
                    meta_url,
                    data=f,
                    headers={"Accept": "application/json"},
                    timeout=30
                )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    def _html_to_markdown(self, html: str) -> str:
        if MARKDOWNIFY_AVAILABLE:
            return self._convert_with_markdownify(html)
        return self._convert_fallback(html)

    def _convert_with_markdownify(self, html: str) -> str:
        try:
            markdown = md(
                html,
                heading_style="ATX",
                bullets="-",
                strip=["script", "style"],
                convert=["table", "tr", "td", "th", "p", "h1", "h2", "h3", "h4", "ul", "ol", "li", "a", "strong", "em"]
            )
            return self._cleanup_markdown(markdown)
        except Exception:
            return self._convert_fallback(html)

    def _convert_fallback(self, html: str) -> str:
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

        return self._cleanup_markdown(text)

    def _cleanup_markdown(self, text: str) -> str:
        text = re.sub(r'\n{3,}', '\n\n', text)
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()


# =============================================================================
# FEEDBACK TRACKER
# =============================================================================

class FeedbackTracker:
    """Tracker für User-Korrekturen an KI-Klassifikationen."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or FEEDBACK_DB_PATH
        self._init_database()

    def _init_database(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_hash TEXT NOT NULL,
                filename TEXT NOT NULL,
                predicted_category TEXT,
                actual_category TEXT,
                predicted_path TEXT,
                actual_path TEXT,
                predicted_confidence REAL,
                correction_type TEXT DEFAULT 'category',
                user_comment TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_corrections_category
            ON corrections(predicted_category, actual_category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_corrections_timestamp
            ON corrections(timestamp)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS correction_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                predicted_category TEXT NOT NULL,
                actual_category TEXT NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                last_seen TEXT,
                UNIQUE(predicted_category, actual_category)
            )
        """)

        conn.commit()
        conn.close()

    def log_correction(
        self,
        file_hash: str,
        filename: str,
        predicted_category: str,
        actual_category: str,
        predicted_path: Optional[str] = None,
        actual_path: Optional[str] = None,
        predicted_confidence: Optional[float] = None,
        user_comment: Optional[str] = None
    ) -> int:
        if predicted_path and actual_path and predicted_category != actual_category:
            correction_type = "both"
        elif predicted_path and actual_path:
            correction_type = "path"
        else:
            correction_type = "category"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO corrections (
                file_hash, filename, predicted_category, actual_category,
                predicted_path, actual_path, predicted_confidence,
                correction_type, user_comment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_hash, filename, predicted_category, actual_category,
            predicted_path, actual_path, predicted_confidence,
            correction_type, user_comment
        ))

        correction_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO correction_patterns (predicted_category, actual_category, last_seen)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(predicted_category, actual_category) DO UPDATE SET
                occurrence_count = occurrence_count + 1,
                last_seen = datetime('now')
        """, (predicted_category, actual_category))

        conn.commit()
        conn.close()

        return correction_id

    def get_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM corrections")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT correction_type, COUNT(*)
            FROM corrections
            GROUP BY correction_type
        """)
        by_type = dict(cursor.fetchall())

        cursor.execute("""
            SELECT predicted_category, actual_category, occurrence_count
            FROM correction_patterns
            ORDER BY occurrence_count DESC
            LIMIT 10
        """)
        top_patterns = [
            {"predicted": row[0], "actual": row[1], "count": row[2]}
            for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT strftime('%Y-W%W', timestamp) as week, COUNT(*)
            FROM corrections
            GROUP BY week
            ORDER BY week DESC
            LIMIT 12
        """)
        by_week = dict(cursor.fetchall())

        conn.close()

        return {
            "total_corrections": total,
            "by_type": by_type,
            "top_misclassifications": top_patterns,
            "corrections_by_week": by_week
        }

    def get_confusion_matrix(self) -> Dict[str, Dict[str, int]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT predicted_category, actual_category, COUNT(*)
            FROM corrections
            GROUP BY predicted_category, actual_category
        """)

        confusion = {}
        for row in cursor.fetchall():
            predicted, actual, count = row
            if predicted not in confusion:
                confusion[predicted] = {}
            confusion[predicted][actual] = count

        conn.close()
        return confusion


# =============================================================================
# MEILISEARCH CLIENT
# =============================================================================

class MeilisearchClient:
    """Client für Meilisearch-Operationen."""

    def __init__(self, url: str = None, api_key: str = None):
        self.url = url or MEILISEARCH_URL
        self.api_key = api_key or MEILISEARCH_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def health(self) -> bool:
        try:
            response = requests.get(f"{self.url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def search(
        self,
        query: str,
        filters: Optional[str] = None,
        sort: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
        attributes_to_retrieve: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        payload = {
            "q": query,
            "limit": limit,
            "offset": offset
        }

        if filters:
            payload["filter"] = filters
        if sort:
            payload["sort"] = sort
        if attributes_to_retrieve:
            payload["attributesToRetrieve"] = attributes_to_retrieve

        response = requests.post(
            f"{self.url}/indexes/{INDEX_NAME}/search",
            headers=self.headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "hits": result.get("hits", []),
                "total": result.get("estimatedTotalHits", 0),
                "processing_time_ms": result.get("processingTimeMs", 0),
                "query": query
            }

        raise HTTPException(status_code=response.status_code, detail=response.text)

    def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Prepare documents with timestamp fields
        prepared = [self._prepare_document(doc) for doc in documents]

        response = requests.post(
            f"{self.url}/indexes/{INDEX_NAME}/documents",
            headers=self.headers,
            json=prepared,
            timeout=60
        )

        if response.status_code in (200, 202):
            return response.json()

        raise HTTPException(status_code=response.status_code, detail=response.text)

    def _prepare_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Bereitet ein Dokument für die Indexierung vor."""
        result = doc.copy()

        for field, ts_field in [
            ("file_created", "file_created_timestamp"),
            ("file_modified", "file_modified_timestamp"),
            ("indexed_at", "indexed_at_timestamp")
        ]:
            if field in doc and doc[field]:
                try:
                    dt = datetime.fromisoformat(doc[field].replace("Z", "+00:00"))
                    result[ts_field] = int(dt.timestamp())

                    if field == "file_created":
                        result["year_created"] = dt.year
                        result["month_created"] = dt.month
                        result["weekday_created"] = dt.weekday()
                        result["hour_created"] = dt.hour
                except Exception:
                    pass

        if "entities" in doc and isinstance(doc["entities"], dict):
            flat_parts = []
            for key, value in doc["entities"].items():
                if isinstance(value, list):
                    flat_parts.extend([str(v) for v in value])
                elif value:
                    flat_parts.append(str(value))
            result["entities_flat"] = " ".join(flat_parts)

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

        return result

    def get_stats(self) -> Optional[Dict]:
        try:
            response = requests.get(
                f"{self.url}/indexes/{INDEX_NAME}/stats",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    def setup_index(self, reset: bool = False) -> bool:
        """Konfiguriert den Index mit optimalen Einstellungen."""
        if reset:
            try:
                requests.delete(
                    f"{self.url}/indexes/{INDEX_NAME}",
                    headers=self.headers,
                    timeout=10
                )
            except Exception:
                pass

        # Create index
        try:
            requests.post(
                f"{self.url}/indexes",
                headers=self.headers,
                json={"uid": INDEX_NAME, "primaryKey": "id"},
                timeout=10
            )
        except Exception:
            pass

        # Configure settings
        settings = {
            "searchableAttributes": [
                "original_filename",
                "current_filename",
                "extracted_text",
                "meta_description",
                "tags",
                "category",
                "subcategory",
                "entities_flat"
            ],
            "filterableAttributes": [
                "category",
                "subcategory",
                "extension",
                "mime_type",
                "file_created_timestamp",
                "file_modified_timestamp",
                "indexed_at_timestamp",
                "file_size",
                "confidence",
                "status",
                "source_type",
                "year_created",
                "month_created",
                "weekday_created",
                "hour_created"
            ],
            "sortableAttributes": [
                "file_created_timestamp",
                "file_modified_timestamp",
                "indexed_at_timestamp",
                "file_size",
                "confidence",
                "original_filename"
            ],
            "rankingRules": [
                "words",
                "typo",
                "proximity",
                "attribute",
                "sort",
                "exactness",
                "confidence:desc"
            ],
            "typoTolerance": {
                "enabled": True,
                "minWordSizeForTypos": {"oneTypo": 4, "twoTypos": 8},
                "disableOnAttributes": ["id", "sha256", "extension"]
            },
            "synonyms": {
                "rechnung": ["invoice", "bill", "beleg"],
                "vertrag": ["contract", "agreement", "kontrakt"],
                "foto": ["photo", "bild", "image"],
                "video": ["film", "clip", "aufnahme"],
                "email": ["e-mail", "mail", "nachricht"],
                "dokument": ["document", "datei", "file"]
            }
        }

        response = requests.patch(
            f"{self.url}/indexes/{INDEX_NAME}/settings",
            headers=self.headers,
            json=settings,
            timeout=30
        )

        return response.status_code in (200, 202)


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Neural Vault API",
    description="Zentraler API-Service für Neural Vault Dokumenten-Intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
tika_extractor = TikaExtractor()
feedback_tracker = FeedbackTracker()
meilisearch = MeilisearchClient()


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health Check für alle Services."""
    services = {
        "meilisearch": meilisearch.health(),
        "tika": False,
        "redis": False,
        "qdrant": False,
        "ollama": False
    }

    # Check Tika
    try:
        response = requests.get(TIKA_URL.replace("/tika", "/tika"), timeout=5)
        services["tika"] = response.status_code == 200
    except Exception:
        pass

    # Check Redis
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
        services["redis"] = r.ping()
    except Exception:
        pass

    # Check Qdrant
    try:
        headers = {}
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
        if QDRANT_API_KEY:
            headers["api-key"] = QDRANT_API_KEY
            
        response = requests.get(f"{QDRANT_URL}/collections", headers=headers, timeout=5)
        services["qdrant"] = response.status_code == 200
    except Exception:
        pass

    # Check Ollama
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        services["ollama"] = response.status_code == 200
    except Exception:
        pass

    all_healthy = all(services.values())

    return HealthStatus(
        status="healthy" if all_healthy else "degraded",
        services=services,
        timestamp=datetime.now().isoformat()
    )


@app.post("/search", response_model=SearchResult)
async def search(request: SearchRequest):
    """Volltextsuche mit Meilisearch."""
    return meilisearch.search(
        query=request.query,
        filters=request.filters,
        sort=request.sort,
        limit=request.limit,
        offset=request.offset,
        attributes_to_retrieve=request.attributes_to_retrieve
    )


@app.get("/search/pattern-of-life")
async def pattern_of_life_search(
    year: Optional[int] = None,
    month: Optional[int] = Query(None, ge=1, le=12),
    weekday: Optional[int] = Query(None, ge=0, le=6),
    hour_min: Optional[int] = Query(None, ge=0, le=23),
    hour_max: Optional[int] = Query(None, ge=0, le=23),
    category: Optional[str] = None,
    limit: int = 50
):
    """Pattern-of-Life Suche: Dateien nach Erstellungszeitmustern filtern."""
    filters = []

    if year:
        filters.append(f"year_created = {year}")
    if month:
        filters.append(f"month_created = {month}")
    if weekday is not None:
        filters.append(f"weekday_created = {weekday}")
    if hour_min is not None:
        filters.append(f"hour_created >= {hour_min}")
    if hour_max is not None:
        filters.append(f"hour_created <= {hour_max}")
    if category:
        filters.append(f'category = "{category}"')

    filter_str = " AND ".join(filters) if filters else None

    return meilisearch.search(
        query="*",
        filters=filter_str,
        sort=["file_created_timestamp:desc"],
        limit=limit
    )


@app.post("/feedback", response_model=Dict[str, Any])
async def log_feedback(request: FeedbackRequest):
    """Protokolliert eine User-Korrektur."""
    correction_id = feedback_tracker.log_correction(
        file_hash=request.file_hash,
        filename=request.filename,
        predicted_category=request.predicted_category,
        actual_category=request.actual_category,
        predicted_path=request.predicted_path,
        actual_path=request.actual_path,
        predicted_confidence=request.predicted_confidence,
        user_comment=request.user_comment
    )

    return {
        "success": True,
        "correction_id": correction_id,
        "message": f"Korrektur protokolliert: {request.predicted_category} -> {request.actual_category}"
    }


@app.get("/feedback/stats", response_model=FeedbackStats)
async def get_feedback_stats():
    """Statistiken über User-Korrekturen."""
    stats = feedback_tracker.get_stats()
    return FeedbackStats(**stats)


@app.get("/feedback/confusion-matrix")
async def get_confusion_matrix():
    """Confusion Matrix für Kategorien."""
    return feedback_tracker.get_confusion_matrix()


@app.post("/extract", response_model=ExtractResult)
async def extract_document(request: ExtractRequest):
    """Extrahiert Text aus einem Dokument via Tika."""
    result = tika_extractor.extract(
        filepath=Path(request.file_path),
        prefer_markdown=request.prefer_markdown,
        include_metadata=request.include_metadata
    )

    return ExtractResult(
        text=result.get("text", ""),
        format=result.get("format", "unknown"),
        metadata=result.get("metadata"),
        success=result.get("success", False),
        error=result.get("error")
    )


@app.post("/extract/with-context")
async def extract_with_context(
    file_path: str,
    category: Optional[str] = None,
    confidence: Optional[float] = None
):
    """Extrahiert Text und fügt Context Header hinzu."""
    path = Path(file_path)
    result = tika_extractor.extract(filepath=path, prefer_markdown=True)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    wrapped = create_chunk_for_rag(
        text=result["text"],
        filename=path.name,
        category=category,
        confidence=confidence
    )

    return {
        "text": wrapped,
        "original_length": len(result["text"]),
        "wrapped_length": len(wrapped),
        "format": result.get("format")
    }


@app.post("/index/documents")
async def index_documents(request: IndexDocumentRequest):
    """Indexiert Dokumente in Meilisearch."""
    return meilisearch.index_documents(request.documents)


@app.post("/index/setup")
async def setup_index(reset: bool = False):
    """Konfiguriert den Meilisearch-Index."""
    success = meilisearch.setup_index(reset=reset)

    if success:
        return {"success": True, "message": "Index erfolgreich konfiguriert"}

    raise HTTPException(status_code=500, detail="Index-Setup fehlgeschlagen")


@app.get("/index/stats")
async def get_index_stats():
    """Statistiken des Meilisearch-Index."""
    stats = meilisearch.get_stats()
    if stats:
        return stats
    raise HTTPException(status_code=503, detail="Meilisearch nicht erreichbar")


@app.get("/chunk/wrap")
async def wrap_text_chunk(
    text: str,
    filename: str,
    source_type: str = "unknown",
    page: Optional[int] = None,
    category: Optional[str] = None,
    confidence: Optional[float] = None
):
    """Fügt Context Header zu einem Text-Chunk hinzu."""
    try:
        st = SourceType(source_type)
    except ValueError:
        st = SourceType.UNKNOWN

    location = ChunkLocation(page=page) if page else None

    wrapped = wrap_chunk(
        text=text,
        source_type=st,
        filename=filename,
        location=location,
        category=category,
        confidence=confidence
    )

    return {"wrapped_text": wrapped}


# =============================================================================
# RAG ENDPOINTS (für Perplexica Integration)
# =============================================================================

class LocalSearchRequest(BaseModel):
    """Request für lokale Dokumenten-Suche via Qdrant."""
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)
    source_types: Optional[List[str]] = None  # ["document", "audio", "video", "image"]
    include_web: bool = False  # Hybrid-Modus

class SourcePreview(BaseModel):
    """Source-Preview mit Timecodes/Seitenangaben."""
    id: str
    filename: str
    source_type: str  # document, audio, video, image
    text_snippet: str
    confidence: float
    # Für Audio/Video
    timecode_start: Optional[str] = None
    timecode_end: Optional[str] = None
    # Für Dokumente
    page_number: Optional[int] = None
    total_pages: Optional[int] = None
    # Für Bilder
    thumbnail_url: Optional[str] = None
    ocr_text: Optional[str] = None
    # Metadaten
    file_path: str
    indexed_at: Optional[str] = None

class RAGSearchResult(BaseModel):
    """Ergebnis der RAG-Suche mit Quellen."""
    query: str
    sources: List[SourcePreview]
    total_results: int
    processing_time_ms: int


@app.post("/rag/search", response_model=RAGSearchResult)
async def rag_local_search(request: LocalSearchRequest):
    """Lokale Dokumenten-Suche via Qdrant für Perplexica RAG."""
    import time
    start_time = time.time()
    
    sources = []
    
    try:
        # Qdrant Vector Search
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
        headers = {"api-key": QDRANT_API_KEY} if QDRANT_API_KEY else {}
        
        # Einfache Suche (später: Embedding-basiert)
        # Für jetzt: Scroll durch Collection und Filter
        response = requests.post(
            f"{QDRANT_URL}/collections/neural_vault/points/scroll",
            headers=headers,
            json={
                "limit": request.limit,
                "with_payload": True,
                "with_vector": False
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            points = data.get("result", {}).get("points", [])
            
            for point in points:
                payload = point.get("payload", {})
                
                # Source Type ermitteln
                ext = Path(payload.get("filename", "")).suffix.lower()
                if ext in [".mp4", ".mkv", ".avi", ".mov"]:
                    source_type = "video"
                elif ext in [".mp3", ".wav", ".flac", ".m4a"]:
                    source_type = "audio"
                elif ext in [".jpg", ".png", ".tiff", ".bmp"]:
                    source_type = "image"
                else:
                    source_type = "document"
                
                # Filter nach source_types wenn angegeben
                if request.source_types and source_type not in request.source_types:
                    continue
                
                source = SourcePreview(
                    id=str(point.get("id", "")),
                    filename=payload.get("filename", "Unknown"),
                    source_type=source_type,
                    text_snippet=payload.get("text", "")[:300] + "..." if len(payload.get("text", "")) > 300 else payload.get("text", ""),
                    confidence=payload.get("confidence", 0.0),
                    timecode_start=payload.get("timecode_start"),
                    timecode_end=payload.get("timecode_end"),
                    page_number=payload.get("page"),
                    total_pages=payload.get("total_pages"),
                    thumbnail_url=f"/sources/{point.get('id')}/thumbnail" if source_type == "image" else None,
                    ocr_text=payload.get("ocr_text"),
                    file_path=payload.get("file_path", ""),
                    indexed_at=payload.get("indexed_at")
                )
                sources.append(source)
                
    except Exception as e:
        # Fallback: Bei Fehler leere Liste
        pass
    
    processing_time = int((time.time() - start_time) * 1000)
    
    return RAGSearchResult(
        query=request.query,
        sources=sources,
        total_results=len(sources),
        processing_time_ms=processing_time
    )


@app.get("/sources/{source_id}")
async def get_source_details(source_id: str):
    """Detailinformationen zu einer Quelle inkl. Timecodes."""
    try:
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
        headers = {"api-key": QDRANT_API_KEY} if QDRANT_API_KEY else {}
        
        response = requests.get(
            f"{QDRANT_URL}/collections/neural_vault/points/{source_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            payload = data.get("result", {}).get("payload", {})
            
            return {
                "id": source_id,
                "filename": payload.get("filename"),
                "file_path": payload.get("file_path"),
                "text": payload.get("text"),
                "source_type": payload.get("source_type"),
                "timecodes": payload.get("timecodes", []),
                "page": payload.get("page"),
                "total_pages": payload.get("total_pages"),
                "confidence": payload.get("confidence"),
                "extraction_method": payload.get("extraction_method"),
                "indexed_at": payload.get("indexed_at")
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    raise HTTPException(status_code=404, detail="Quelle nicht gefunden")


@app.get("/sources/{source_id}/thumbnail")
async def get_source_thumbnail(source_id: str):
    """Thumbnail-Vorschau für Bilder/Videos."""
    # TODO: Implement actual thumbnail generation
    # For now, return placeholder info
    return {
        "source_id": source_id,
        "thumbnail_available": False,
        "message": "Thumbnail-Generation wird in Phase 5 implementiert"
    }


@app.get("/sources/{source_id}/stream")
async def stream_source_media(
    source_id: str,
    start: Optional[float] = Query(None, description="Start-Position in Sekunden")
):
    """Stream Media-Datei ab bestimmtem Timecode."""
    # TODO: Implement media streaming with range support
    # This will be needed for video/audio player with timecode navigation
    return {
        "source_id": source_id,
        "start_position": start,
        "message": "Media-Streaming wird in Phase 5 implementiert"
    }


# =============================================================================
# STARTUP
# =============================================================================

@app.on_event("startup")
async def startup():
    """Initialisierung beim Start."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Warte auf Meilisearch und konfiguriere Index
    import time
    for _ in range(30):
        if meilisearch.health():
            meilisearch.setup_index()
            break
        time.sleep(1)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
