"""
Neural Vault Extraction Workers
===============================

Spezialisierte Worker für verschiedene Dateitypen.
Implementiert das Assembly-Line Pattern.

Worker-Typen:
- DocumentWorker: PDF, DOCX, XLSX via Tika/Docling
- AudioWorker: MP3, WAV via Whisper
- VideoWorker: MP4, MKV via FFmpeg + Whisper
- ImageWorker: JPG, PNG via Tesseract/PaddleOCR
- EmailWorker: EML, MSG via Parser
- ArchiveWorker: ZIP, RAR via 7-Zip
"""

import os
import json
import asyncio
import hashlib
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod
import logging

import httpx
import redis.asyncio as redis

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "worker": "%(name)s", "message": "%(message)s"}'
)

# =============================================================================
# CONFIGURATION
# =============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Service URLs
# Document Processor (unified Docling + Surya + GLiNER)
DOCUMENT_PROCESSOR_URL = os.getenv("DOCUMENT_PROCESSOR_URL", "http://document-processor:8000")
TIKA_URL = os.getenv("TIKA_URL", "http://tika:9998")  # Fallback
# WhisperX (Word-Level Timestamps + Diarization)
WHISPERX_URL = os.getenv("WHISPERX_URL", "http://whisperx:9000")
WHISPER_URL = os.getenv("WHISPER_URL", WHISPERX_URL)  # Backward compat
WHISPER_FAST_URL = os.getenv("WHISPER_FAST_URL", WHISPERX_URL)
PARSER_URL = os.getenv("PARSER_URL", "http://parser-service:8000")
SPECIAL_PARSER_URL = os.getenv("SPECIAL_PARSER_URL", "http://special-parser:8015")

# Worker Configuration
WORKER_TYPE = os.getenv("WORKER_TYPE", "documents")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "extraction-workers")
CONSUMER_NAME = os.getenv("HOSTNAME", f"worker-{WORKER_TYPE}-1")


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class FileJob:
    """Ein zu verarbeitender Job."""
    id: str
    path: str
    filename: str
    extension: str
    size: int
    modified: str
    mime_type: Optional[str] = None
    priority: int = 50
    created_at: str = None
    processing_path: str = "fast"
    status: str = "pending"
    retries: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "FileJob":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ExtractionResult:
    """Ergebnis einer Extraktion."""
    job_id: str
    file_path: str
    filename: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    confidence: float = 1.0
    extraction_method: str = "unknown"
    processing_time_ms: int = 0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# ERROR CLASSIFICATION SYSTEM
# =============================================================================

from enum import Enum
import traceback
import struct
import zipfile
import subprocess

class ErrorSource(Enum):
    """Fehlerquelle-Klassifikation."""
    SOURCE_FILE = "source_file"      # Problem mit der Quelldatei
    PROCESSING = "processing"         # Problem in der Verarbeitung
    INFRASTRUCTURE = "infrastructure" # Problem mit Services/Infra
    UNKNOWN = "unknown"


class ErrorType(Enum):
    """Detaillierter Fehlertyp."""
    # Quelldatei-Fehler
    FILE_CORRUPTED = "file_corrupted"
    FILE_EMPTY = "file_empty"
    FILE_ENCRYPTED = "file_encrypted"
    FILE_FORMAT_MISMATCH = "file_format_mismatch"
    FILE_UNSUPPORTED = "file_unsupported"
    FILE_NOT_FOUND = "file_not_found"
    FILE_PERMISSION_DENIED = "file_permission_denied"
    
    # Verarbeitungs-Fehler
    EXTRACTION_FAILED = "extraction_failed"
    OCR_FAILED = "ocr_failed"
    TRANSCRIPTION_FAILED = "transcription_failed"
    CONVERSION_FAILED = "conversion_failed"
    PARSING_FAILED = "parsing_failed"
    
    # Infrastruktur-Fehler
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    OUT_OF_MEMORY = "out_of_memory"
    DEPENDENCY_MISSING = "dependency_missing"


@dataclass
class ClassifiedError:
    """Klassifizierter Fehler mit Kontext."""
    source: ErrorSource
    error_type: ErrorType
    message: str
    details: Optional[Dict] = None
    recoverable: bool = True
    retry_recommended: bool = True

    def to_dict(self) -> Dict:
        return {
            'error_source': self.source.value,
            'error_type': self.error_type.value,
            'message': self.message,
            'details': self.details,
            'recoverable': self.recoverable,
            'retry_recommended': self.retry_recommended
        }


class SourceFileValidator:
    """Validiert Quelldateien VOR der Verarbeitung."""
    
    # Bekannte Magic Bytes für Formate
    MAGIC_BYTES = {
        'pdf': b'%PDF',
        'zip': b'PK\x03\x04',
        'rar': b'Rar!\x1a\x07',
        '7z': b"7z\xbc\xaf\x27\x1c",
        'png': b'\x89PNG\r\n\x1a\n',
        'jpg': b'\xff\xd8\xff',
        'jpeg': b'\xff\xd8\xff',
        'gif': b'GIF8',
        'mp3': b'ID3',
        'docx': b'PK\x03\x04',
        'xlsx': b'PK\x03\x04',
        'pptx': b'PK\x03\x04',
    }
    
    def __init__(self):
        self.logger = logging.getLogger("SourceFileValidator")
    
    def validate(self, file_path: str) -> Dict:
        """
        Führt alle Validierungen durch.
        Returns: {valid: bool, errors: list, warnings: list, file_health: str}
        """
        path = Path(file_path)
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_health': 'healthy'
        }
        
        # 1. Existenz
        if not path.exists():
            result['valid'] = False
            result['errors'].append('FILE_NOT_FOUND')
            result['file_health'] = 'missing'
            return result
        
        # 2. Größe
        try:
            size = path.stat().st_size
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'STAT_ERROR: {str(e)}')
            result['file_health'] = 'inaccessible'
            return result
            
        if size == 0:
            result['valid'] = False
            result['errors'].append('EMPTY_FILE')
            result['file_health'] = 'empty'
            return result
        
        if size < 10:
            result['warnings'].append('SUSPICIOUSLY_SMALL')
        
        # 3. Lesbarkeit
        try:
            with open(path, 'rb') as f:
                header = f.read(1024)
        except PermissionError:
            result['valid'] = False
            result['errors'].append('PERMISSION_DENIED')
            result['file_health'] = 'inaccessible'
            return result
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'READ_ERROR: {str(e)}')
            result['file_health'] = 'corrupted'
            return result
        
        # 4. Magic Bytes Check
        ext = path.suffix.lower().replace('.', '')
        expected_magic = self.MAGIC_BYTES.get(ext)
        if expected_magic and not header.startswith(expected_magic):
            result['warnings'].append(f'MAGIC_MISMATCH: Expected {ext} header')
            result['file_health'] = 'mislabeled'
        
        # 5. Format-spezifische Prüfungen
        format_errors = self._check_format_integrity(path, ext, header)
        if format_errors:
            result['errors'].extend(format_errors)
            result['valid'] = False
            result['file_health'] = 'corrupted'
        
        return result
    
    def _check_format_integrity(self, path: Path, ext: str, header: bytes) -> List[str]:
        """Format-spezifische Integritätsprüfungen."""
        errors = []
        
        if ext == 'pdf':
            # PDF muss mit %PDF beginnen
            if not header.startswith(b'%PDF'):
                errors.append('PDF_INVALID_HEADER')
            # Prüfe auf Verschlüsselung
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                    if b'/Encrypt' in content:
                        errors.append('PDF_ENCRYPTED')
                    if b'%%EOF' not in content[-1024:]:
                        errors.append('PDF_TRUNCATED')
            except:
                pass
        
        elif ext in ['zip', 'docx', 'xlsx', 'pptx']:
            try:
                with zipfile.ZipFile(path, 'r') as zf:
                    bad_file = zf.testzip()
                    if bad_file:
                        errors.append(f'ZIP_CRC_ERROR: {bad_file}')
            except zipfile.BadZipFile:
                errors.append('ZIP_CORRUPTED')
            except Exception as e:
                errors.append(f'ZIP_ERROR: {str(e)}')
        
        return errors


class ErrorClassifier:
    """Klassifiziert Fehler basierend auf Fehlermeldungen und Kontext."""
    
    # Muster für Quelldatei-Fehler
    SOURCE_FILE_PATTERNS = {
        ErrorType.FILE_CORRUPTED: [
            'corrupt', 'damaged', 'invalid', 'malformed',
            'unexpected end of file', 'truncated', 'bad crc',
            'cannot identify image file', 'not a valid',
            'moov atom not found', 'invalid data'
        ],
        ErrorType.FILE_EMPTY: [
            'empty file', 'file is empty', 'no content', 
            'zero bytes', 'nothing to extract'
        ],
        ErrorType.FILE_ENCRYPTED: [
            'encrypted', 'password protected', 'password required',
            'decryption failed'
        ],
        ErrorType.FILE_FORMAT_MISMATCH: [
            'format not recognized', 'unsupported format',
            'invalid header', 'magic number mismatch',
            'not a pdf', 'not an image'
        ],
    }
    
    # Muster für Verarbeitungs-Fehler
    PROCESSING_PATTERNS = {
        ErrorType.OCR_FAILED: [
            'ocr error', 'surya error', 'tesseract error',
            'text recognition failed'
        ],
        ErrorType.TRANSCRIPTION_FAILED: [
            'whisper error', 'transcription error',
            'audio processing failed', 'no speech detected'
        ],
        ErrorType.CONVERSION_FAILED: [
            'conversion failed', 'could not convert',
            'pillow error', 'cairo error', 'ffmpeg error'
        ],
    }
    
    # Muster für Infrastruktur-Fehler
    INFRA_PATTERNS = {
        ErrorType.SERVICE_UNAVAILABLE: [
            'connection refused', 'service unavailable',
            '502', '503', '504', 'cannot connect',
            'host unreachable', 'connection reset'
        ],
        ErrorType.TIMEOUT: [
            'timeout', 'timed out', 'deadline exceeded',
            'operation took too long'
        ],
        ErrorType.OUT_OF_MEMORY: [
            'out of memory', 'memory error', 'oom',
            'cannot allocate', 'mmap failed'
        ],
        ErrorType.DEPENDENCY_MISSING: [
            'import error', 'module not found', 
            'library not loaded', 'dll not found',
            'no module named'
        ],
    }
    
    def __init__(self):
        self.logger = logging.getLogger("ErrorClassifier")
    
    def classify(self, exception: Exception, context: Dict = None) -> ClassifiedError:
        """Klassifiziert eine Exception."""
        error_msg = str(exception).lower()
        tb = traceback.format_exc().lower()
        combined = f"{error_msg} {tb}"
        
        # 1. Prüfe auf Quelldatei-Fehler
        for error_type, patterns in self.SOURCE_FILE_PATTERNS.items():
            if any(p in combined for p in patterns):
                return ClassifiedError(
                    source=ErrorSource.SOURCE_FILE,
                    error_type=error_type,
                    message=str(exception),
                    details=context,
                    recoverable=False,
                    retry_recommended=False
                )
        
        # 2. Prüfe auf Infrastruktur-Fehler
        for error_type, patterns in self.INFRA_PATTERNS.items():
            if any(p in combined for p in patterns):
                return ClassifiedError(
                    source=ErrorSource.INFRASTRUCTURE,
                    error_type=error_type,
                    message=str(exception),
                    details=context,
                    recoverable=True,
                    retry_recommended=True
                )
        
        # 3. Prüfe auf Verarbeitungs-Fehler
        for error_type, patterns in self.PROCESSING_PATTERNS.items():
            if any(p in combined for p in patterns):
                return ClassifiedError(
                    source=ErrorSource.PROCESSING,
                    error_type=error_type,
                    message=str(exception),
                    details=context,
                    recoverable=True,
                    retry_recommended=True
                )
        
        # 4. Fallback: Unbekannter Fehler
        return ClassifiedError(
            source=ErrorSource.UNKNOWN,
            error_type=ErrorType.EXTRACTION_FAILED,
            message=str(exception),
            details=context,
            recoverable=True,
            retry_recommended=True
        )


# =============================================================================
# QUEUE MANAGER
# =============================================================================

class QueueManager:
    """Async Redis Queue Manager."""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.logger = logging.getLogger("QueueManager")

    async def connect(self):
        self.redis = await redis.from_url(
            REDIS_URL,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True
        )
        self.logger.info("Connected to Redis")

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def dequeue(self, queue: str, consumer_group: str, consumer: str, count: int = 1) -> List[FileJob]:
        try:
            try:
                await self.redis.xgroup_create(queue, consumer_group, id="0", mkstream=True)
            except redis.ResponseError:
                pass

            messages = await self.redis.xreadgroup(
                consumer_group, consumer, {queue: ">"}, count=count, block=5000
            )

            jobs = []
            for stream, entries in messages:
                for entry_id, data in entries:
                    job_data = json.loads(data.get("data", "{}"))
                    job = FileJob.from_dict(job_data)
                    job.id = entry_id
                    jobs.append(job)
            return jobs

        except Exception as e:
            self.logger.error(f"Dequeue error: {e}")
            return []

    async def enqueue(self, queue: str, data: Dict) -> str:
        return await self.redis.xadd(queue, {"data": json.dumps(data)}, maxlen=10000)

    async def ack(self, queue: str, consumer_group: str, message_id: str):
        await self.redis.xack(queue, consumer_group, message_id)

    async def move_to_dlq(self, dlq: str, job: FileJob, error: str):
        job.status = "failed"
        job.error = error
        job.retries += 1
        await self.enqueue(dlq, job.to_dict())

    async def move_to_dlq_classified(self, dlq: str, job: FileJob, classified_error: ClassifiedError):
        """Sendet Job mit klassifiziertem Fehler an DLQ."""
        job.status = "failed"
        job.error = classified_error.message
        job.retries += 1
        
        # Erweiterte DLQ-Daten mit Klassifikation
        dlq_data = {
            **job.to_dict(),
            'error_source': classified_error.source.value,
            'error_type': classified_error.error_type.value,
            'recoverable': classified_error.recoverable,
            'retry_recommended': classified_error.retry_recommended,
            'classification_details': classified_error.details
        }
        await self.enqueue(dlq, dlq_data)


# =============================================================================
# BASE WORKER
# =============================================================================

class BaseExtractionWorker(ABC):
    """Basisklasse für alle Extraction Workers."""

    MAX_RETRIES = 3  # Maximale Retry-Versuche
    
    def __init__(
        self,
        input_queue: str,
        output_queue: str,
        dlq: str,
        worker_name: str
    ):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.dlq = dlq
        self.worker_name = worker_name
        self.queue_manager = QueueManager()
        self.http_client: Optional[httpx.AsyncClient] = None
        self.running = False
        self.logger = logging.getLogger(worker_name)
        
        # Error Classification System
        self.file_validator = SourceFileValidator()
        self.error_classifier = ErrorClassifier()

    async def start(self):
        await self.queue_manager.connect()
        self.http_client = httpx.AsyncClient(timeout=300.0)
        self.running = True
        self.logger.info(f"Worker started, listening on {self.input_queue}")

        while self.running:
            try:
                jobs = await self.queue_manager.dequeue(
                    self.input_queue, CONSUMER_GROUP, self.worker_name, count=1
                )

                for job in jobs:
                    start_time = datetime.now()
                    try:
                        self.logger.info(f"Processing: {job.filename}")

                        # Datei lokal kopieren (vermeidet SMB-Lock-Probleme)
                        local_path = await self._copy_to_local(job.path)

                        try:
                            # Extraktion durchführen
                            result = await self.extract(job, local_path)
                            result.processing_time_ms = int(
                                (datetime.now() - start_time).total_seconds() * 1000
                            )

                            # In Output Queue schreiben
                            await self.queue_manager.enqueue(
                                self.output_queue, result.to_dict()
                            )

                            # Als verarbeitet markieren
                            await self.queue_manager.ack(
                                self.input_queue, CONSUMER_GROUP, job.id
                            )

                            self.logger.info(
                                f"Completed: {job.filename} in {result.processing_time_ms}ms"
                            )

                        finally:
                            # Lokale Kopie löschen
                            await self._cleanup_local(local_path)

                    except Exception as e:
                        # Fehler klassifizieren
                        classified = self.error_classifier.classify(
                            exception=e,
                            context={
                                'file_path': job.path,
                                'extension': job.extension,
                                'worker': self.worker_name,
                                'retries': job.retries
                            }
                        )
                        
                        self.logger.error(
                            f"Error processing {job.filename}: "
                            f"source={classified.source.value}, "
                            f"type={classified.error_type.value}, "
                            f"retry={classified.retry_recommended}"
                        )
                        
                        # Entscheidung: Retry oder DLQ?
                        if classified.retry_recommended and job.retries < self.MAX_RETRIES:
                            # Re-queue für Retry
                            self.logger.info(f"Scheduling retry {job.retries + 1}/{self.MAX_RETRIES} for {job.filename}")
                            job.retries += 1
                            await self.queue_manager.enqueue(self.input_queue, job.to_dict())
                        else:
                            # Ab in DLQ mit Klassifikation
                            await self.queue_manager.move_to_dlq_classified(self.dlq, job, classified)
                        
                        await self.queue_manager.ack(
                            self.input_queue, CONSUMER_GROUP, job.id
                        )

            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        self.running = False
        if self.http_client:
            await self.http_client.aclose()
        await self.queue_manager.disconnect()

    def _translate_path(self, source_path: str) -> str:
        """
        Cross-platform path translation for Docker volume mounts.
        
        Auto-detects path format and translates to container paths:
        - Windows: F:\\path\\file → /mnt/data/path/file (if HOST_MOUNT_PREFIX set)
        - macOS:   /Users/... → /mnt/data/... (if mapped)
        - Linux:   Already correct format, passed through
        
        Environment variables:
        - HOST_MOUNT_PREFIX: The host path prefix to strip (e.g., 'F:' or '/Users/john')
        - CONTAINER_MOUNT_PATH: The container mount point (default: '/mnt/data')
        """
        import re
        
        host_prefix = os.getenv('HOST_MOUNT_PREFIX', '')
        container_path = os.getenv('CONTAINER_MOUNT_PATH', '/mnt/data')
        
        # Detect path format
        # Windows absolute path: starts with drive letter (C:, D:, F:, etc.)
        windows_match = re.match(r'^([A-Za-z]):[/\\]', source_path)
        
        if windows_match:
            # Windows path detected - convert to Linux format
            # F:\_Inbox\file.txt → /mnt/data/_Inbox/file.txt
            drive = windows_match.group(1).upper()
            # Strip drive letter and convert backslashes
            linux_path = source_path[2:].replace('\\', '/')
            
            # Use host prefix if set, otherwise use default /mnt/data
            if host_prefix and host_prefix.upper().startswith(drive + ':'):
                # HOST_MOUNT_PREFIX matches the drive, use CONTAINER_MOUNT_PATH
                return container_path + linux_path
            else:
                # Default: assume F:/ is mounted as /mnt/data
                return '/mnt/data' + linux_path
        
        elif source_path.startswith('/') and not source_path.startswith('/mnt/'):
            # Unix absolute path (Linux/macOS) - check if needs translation
            if host_prefix and source_path.startswith(host_prefix):
                # Translate host prefix to container mount
                return container_path + source_path[len(host_prefix):]
        
        # Already a container path or relative path - pass through
        return source_path

    async def _copy_to_local(self, source_path: str) -> Path:
        """Kopiert Datei in lokales temp-Verzeichnis."""
        # Cross-platform path translation for Docker volume mounts
        translated_path = self._translate_path(source_path)
        
        source = Path(translated_path)
        temp_dir = Path(tempfile.gettempdir()) / "extraction"
        temp_dir.mkdir(exist_ok=True)

        local_path = temp_dir / f"{hashlib.md5(source_path.encode()).hexdigest()}_{source.name}"
        shutil.copy2(source, local_path)
        return local_path

    async def _cleanup_local(self, local_path: Path):
        """Löscht lokale Kopie."""
        try:
            local_path.unlink()
        except Exception:
            pass

    @abstractmethod
    async def extract(self, job: FileJob, local_path: Path) -> ExtractionResult:
        """Extraktion durchführen - muss von Subklassen implementiert werden."""
        pass


# =============================================================================
# DOCUMENT WORKER (PDF, DOCX, XLSX)
# =============================================================================

class DocumentWorker(BaseExtractionWorker):
    """Verarbeitet Dokumente via Document Processor (Docling) oder Tika Fallback."""

    def __init__(self):
        super().__init__(
            input_queue="extract:documents",
            output_queue="enrich:ner",
            dlq="dlq:extract",
            worker_name=f"document-worker-{CONSUMER_NAME}"
        )

    async def extract(self, job: FileJob, local_path: Path) -> ExtractionResult:
        # Primary: Document Processor (Docling - 97.9% Table Accuracy)
        try:
            return await self._extract_docling(job, local_path)
        except Exception as e:
            self.logger.warning(f"Docling failed, falling back to Tika: {e}")
            # Fallback: Tika
            if job.processing_path == "deep":
                return await self._extract_tika_deep(job, local_path)
            return await self._extract_tika_fast(job, local_path)

    async def _extract_docling(self, job: FileJob, local_path: Path) -> ExtractionResult:
        """Primary: Document Processor (Docling - 97.9% Table Accuracy)."""
        with open(local_path, "rb") as f:
            files = {"file": (job.filename, f)}
            response = await self.http_client.post(
                f"{DOCUMENT_PROCESSOR_URL}/process/document",
                files=files,
                params={"processor": "auto"}
            )

        if response.status_code != 200:
            raise Exception(f"Document Processor error: {response.status_code}")

        result = response.json()

        return ExtractionResult(
            job_id=job.id,
            file_path=job.path,
            filename=job.filename,
            text=result.get("text", ""),
            metadata={
                "tables_count": result.get("tables_count", 0),
                "pages": result.get("pages", 0),
                "processor": result.get("processor", "docling"),
            },
            extraction_method=f"docling-{result.get('processor', 'auto')}",
            confidence=result.get("confidence", 0.979)
        )

    async def _extract_tika_fast(self, job: FileJob, local_path: Path) -> ExtractionResult:
        """Fallback Fast: Tika Plain Text."""
        with open(local_path, "rb") as f:
            response = await self.http_client.put(
                f"{TIKA_URL}/tika",
                content=f.read(),
                headers={"Accept": "text/plain"}
            )

        text = response.text if response.status_code == 200 else ""

        return ExtractionResult(
            job_id=job.id,
            file_path=job.path,
            filename=job.filename,
            text=text.strip(),
            extraction_method="tika-fast-fallback",
            confidence=0.75
        )

    async def _extract_tika_deep(self, job: FileJob, local_path: Path) -> ExtractionResult:
        """Fallback Deep: Tika HTML → Markdown."""
        with open(local_path, "rb") as f:
            response = await self.http_client.put(
                f"{TIKA_URL}/tika",
                content=f.read(),
                headers={"Accept": "text/html"}
            )

        html = response.text if response.status_code == 200 else ""
        text = self._html_to_markdown(html)

        return ExtractionResult(
            job_id=job.id,
            file_path=job.path,
            filename=job.filename,
            text=text,
            extraction_method="tika-deep-fallback",
            confidence=0.80
        )

    def _html_to_markdown(self, html: str) -> str:
        """Konvertiert HTML zu Markdown."""
        import re
        import html as html_module

        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = html_module.unescape(text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()


# =============================================================================
# AUDIO WORKER (MP3, WAV, M4A)
# =============================================================================

class AudioWorker(BaseExtractionWorker):
    """Verarbeitet Audio via Whisper."""

    def __init__(self):
        super().__init__(
            input_queue="extract:audio",
            output_queue="enrich:ner",
            dlq="dlq:extract",
            worker_name=f"audio-worker-{CONSUMER_NAME}"
        )

    async def extract(self, job: FileJob, local_path: Path) -> ExtractionResult:
        # Wähle Whisper-Instanz basierend auf Processing Path
        whisper_url = WHISPER_URL if job.processing_path == "deep" else WHISPER_FAST_URL

        with open(local_path, "rb") as f:
            files = {"file": (job.filename, f, "audio/mpeg")}
            response = await self.http_client.post(
                f"{whisper_url}/v1/audio/transcriptions",
                files=files,
                data={"language": "de", "response_format": "verbose_json"}
            )

        if response.status_code != 200:
            raise Exception(f"Whisper error: {response.status_code}")

        result = response.json()
        text = result.get("text", "")

        # Timestamps extrahieren wenn verfügbar
        segments = result.get("segments", [])
        metadata = {
            "duration": result.get("duration"),
            "language": result.get("language"),
            "segments_count": len(segments)
        }

        return ExtractionResult(
            job_id=job.id,
            file_path=job.path,
            filename=job.filename,
            text=text,
            metadata=metadata,
            extraction_method=f"whisper-{'large' if job.processing_path == 'deep' else 'base'}",
            confidence=0.93
        )


# =============================================================================
# IMAGE WORKER (JPG, PNG, TIFF)
# =============================================================================

class ImageWorker(BaseExtractionWorker):
    """Verarbeitet Bilder via Surya OCR (97.7% Accuracy)."""

    def __init__(self):
        super().__init__(
            input_queue="extract:images",
            output_queue="enrich:ner",
            dlq="dlq:extract",
            worker_name=f"image-worker-{CONSUMER_NAME}"
        )

    async def extract(self, job: FileJob, local_path: Path) -> ExtractionResult:
        # Primary: Surya OCR via Document Processor (97.7% Accuracy)
        try:
            # Handle formats needing conversion (HEIC, SVG)
            ext = job.extension.lower().replace(".", "")
            ocr_path = local_path
            
            if ext in ["heic", "heif"]:
                try:
                    from pillow_heif import register_heif_opener
                    from PIL import Image
                    register_heif_opener()
                    img = Image.open(local_path)
                    ocr_path = local_path.with_suffix(".png")
                    img.save(ocr_path, format="PNG")
                    self.logger.info(f"Converted HEIC to PNG: {ocr_path}")
                except ImportError:
                    self.logger.warning("pillow-heif not installed, skipping conversion")
            
            elif ext == "svg":
                try:
                    import cairosvg
                    ocr_path = local_path.with_suffix(".png")
                    cairosvg.svg2png(url=str(local_path), write_to=str(ocr_path))
                    self.logger.info(f"Converted SVG to PNG: {ocr_path}")
                except ImportError:
                    self.logger.warning("cairosvg not installed, skipping conversion")
            
            return await self._extract_surya(job, ocr_path)
        except Exception as e:
            self.logger.warning(f"Surya OCR failed: {e}")
            # No fallback - Tesseract deprecated
            raise

    async def _extract_surya(self, job: FileJob, local_path: Path) -> ExtractionResult:
        """Surya OCR via Document Processor (97.7% Accuracy)."""
        with open(local_path, "rb") as f:
            files = {"file": (job.filename, f)}
            response = await self.http_client.post(
                f"{DOCUMENT_PROCESSOR_URL}/ocr",  # Surya uses /ocr endpoint
                files=files,
                params={"langs": "de,en"}
            )

        if response.status_code != 200:
            raise Exception(f"Surya OCR error: {response.status_code}")

        result = response.json()

        # Extract text from lines
        text = result.get("text", "")
        lines = result.get("lines", [])

        return ExtractionResult(
            job_id=job.id,
            file_path=job.path,
            filename=job.filename,
            text=text,
            metadata={
                "lines_count": len(lines),
                "processor": result.get("processor", "surya"),
                "width": result.get("metadata", {}).get("width", 0),
                "height": result.get("metadata", {}).get("height", 0),
            },
            extraction_method="surya-ocr",
            confidence=result.get("confidence", 0.977)
        )


# =============================================================================
# VIDEO WORKER (MP4, MKV, AVI)
# =============================================================================

class VideoWorker(BaseExtractionWorker):
    """Verarbeitet Video: Extrahiert Audio-Track → Whisper."""

    def __init__(self):
        super().__init__(
            input_queue="extract:video",
            output_queue="enrich:ner",
            dlq="dlq:extract",
            worker_name=f"video-worker-{CONSUMER_NAME}"
        )

    async def extract(self, job: FileJob, local_path: Path) -> ExtractionResult:
        import subprocess

        # 1. Audio-Track extrahieren (FFmpeg now installed directly in container)
        audio_path = local_path.with_suffix(".wav")

        subprocess.run([
            "ffmpeg", "-y", "-i", str(local_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            str(audio_path)
        ], capture_output=True, timeout=300)

        # 2. Video-Metadaten extrahieren
        metadata_result = subprocess.run([
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(local_path)
        ], capture_output=True, text=True, timeout=60)

        metadata = {}
        try:
            metadata = json.loads(metadata_result.stdout)
        except Exception:
            pass

        # 3. Audio transkribieren
        text = ""
        if audio_path.exists():
            with open(audio_path, "rb") as f:
                whisper_url = WHISPER_URL if job.processing_path == "deep" else WHISPER_FAST_URL
                files = {"file": (audio_path.name, f, "audio/wav")}
                response = await self.http_client.post(
                    f"{whisper_url}/v1/audio/transcriptions",
                    files=files,
                    data={"language": "de"}
                )
                if response.status_code == 200:
                    text = response.json().get("text", "")

            # Cleanup
            audio_path.unlink()

        return ExtractionResult(
            job_id=job.id,
            file_path=job.path,
            filename=job.filename,
            text=text,
            metadata=metadata,
            extraction_method="ffmpeg+whisper",
            confidence=0.90
        )


# =============================================================================
# EMAIL WORKER (EML, MSG)
# =============================================================================

class EmailWorker(BaseExtractionWorker):
    """Verarbeitet E-Mails direkt via Python email library."""

    def __init__(self):
        super().__init__(
            input_queue="extract:email",
            output_queue="enrich:ner",
            dlq="dlq:extract",
            worker_name=f"email-worker-{CONSUMER_NAME}"
        )

    async def extract(self, job: FileJob, local_path: Path) -> ExtractionResult:
        import email
        from email import policy
        from email.parser import BytesParser
        
        # Parse EML file directly
        with open(local_path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)
        
        # Extract email fields
        subject = msg.get("subject", "")
        sender = msg.get("from", "")
        to = msg.get("to", "")
        date = msg.get("date", "")
        
        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_content()
                    break
        else:
            body = msg.get_content() if hasattr(msg, 'get_content') else msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        # Build text representation
        text_parts = []
        if subject:
            text_parts.append(f"Betreff: {subject}")
        if sender:
            text_parts.append(f"Von: {sender}")
        if to:
            text_parts.append(f"An: {to}")
        if date:
            text_parts.append(f"Datum: {date}")
        text_parts.append("")
        if body:
            text_parts.append(body)

        text = "\n".join(text_parts)

        return ExtractionResult(
            job_id=job.id,
            file_path=job.path,
            filename=job.filename,
            text=text,
            metadata={
                "subject": subject,
                "from": sender,
                "to": to,
                "date": date,
            },
            entities={
                "emails": [sender, to] if sender else []
            },
            extraction_method="python-email",
            confidence=1.0
        )


# =============================================================================
# ARCHIVE WORKER (ZIP, RAR, 7Z)
# =============================================================================

class ArchiveWorker(BaseExtractionWorker):
    """Verarbeitet Archive direkt via Python zipfile/tarfile module."""

    def __init__(self):
        super().__init__(
            input_queue="extract:archive",
            output_queue="enrich:ner",
            dlq="dlq:extract",
            worker_name=f"archive-worker-{CONSUMER_NAME}"
        )

    async def extract(self, job: FileJob, local_path: Path) -> ExtractionResult:
        import zipfile
        import tarfile
        
        files = []
        archive_type = "unknown"
        
        # Try ZIP format
        if zipfile.is_zipfile(local_path):
            archive_type = "zip"
            try:
                with zipfile.ZipFile(local_path, 'r') as zf:
                    for info in zf.infolist():
                        if not info.is_dir():
                            files.append(info.filename)
            except Exception as e:
                self.logger.warning(f"ZIP read error: {e}")
        
        # Try TAR format (tar, tar.gz, tar.bz2)
        elif tarfile.is_tarfile(local_path):
            archive_type = "tar"
            try:
                with tarfile.open(local_path, 'r:*') as tf:
                    for member in tf.getmembers():
                        if member.isfile():
                            files.append(member.name)
            except Exception as e:
                self.logger.warning(f"TAR read error: {e}")
        
        # RAR and 7Z need external libraries - list as unsupported
        else:
            ext = local_path.suffix.lower()
            if ext in ['.rar', '.7z']:
                archive_type = ext[1:]
                # Can't list contents without external lib, but acknowledge the file
                files = [f"(Archiv-Inhalt nicht lesbar ohne {ext.upper()} Unterstützung)"]
            else:
                raise Exception(f"Unsupported archive format: {ext}")

        text = f"Archiv: {job.filename}\n"
        text += f"Typ: {archive_type.upper()}\n"
        text += f"Enthält {len(files)} Dateien:\n"
        text += "\n".join(f"- {f}" for f in files[:100])
        if len(files) > 100:
            text += f"\n... und {len(files) - 100} weitere Dateien"

        return ExtractionResult(
            job_id=job.id,
            file_path=job.path,
            filename=job.filename,
            text=text,
            metadata={
                "archive_type": archive_type,
                "file_count": len(files),
                "files": files[:100]
            },
            extraction_method=f"python-{archive_type}",
            confidence=1.0
        )


# =============================================================================
# SPECIAL PARSER WORKERS (3D, CAD, GIS, Fonts)
# =============================================================================

class SpecialParserWorker(BaseExtractionWorker):
    """Verarbeitet Spezialformate via Special Parser Service."""

    def __init__(self, category: str, input_queue: str):
        self.category = category
        super().__init__(
            input_queue=input_queue,
            output_queue="enrich:ner",
            dlq="dlq:extract",
            worker_name=f"special-{category}-worker-{CONSUMER_NAME}"
        )

    async def extract(self, job: FileJob, local_path: Path) -> ExtractionResult:
        with open(local_path, "rb") as f:
            files = {"file": (job.filename, f)}
            response = await self.http_client.post(
                f"{SPECIAL_PARSER_URL}/parse",
                files=files,
                params={"category": self.category}
            )

        if response.status_code != 200:
            raise Exception(f"Special parser error: {response.status_code} {response.text}")

        payload = response.json()
        derived_text = payload.get("derived_text", "")
        preview = payload.get("preview", "")
        text = derived_text or preview

        metadata = payload.get("metadata", {})
        metadata.update(
            {
                "preview": preview,
                "category": payload.get("category", self.category),
                "parser": payload.get("parser", "special-parser"),
            }
        )

        return ExtractionResult(
            job_id=job.id,
            file_path=job.path,
            filename=job.filename,
            text=text,
            metadata=metadata,
            extraction_method=payload.get("parser", "special-parser"),
            confidence=payload.get("confidence", 0.6)
        )


class ThreeDWorker(SpecialParserWorker):
    def __init__(self):
        super().__init__(category="3d", input_queue="extract:3d")


class CadWorker(SpecialParserWorker):
    def __init__(self):
        super().__init__(category="cad", input_queue="extract:cad")


class GisWorker(SpecialParserWorker):
    def __init__(self):
        super().__init__(category="gis", input_queue="extract:gis")


class FontsWorker(SpecialParserWorker):
    def __init__(self):
        super().__init__(category="fonts", input_queue="extract:fonts")


# =============================================================================
# WORKER FACTORY
# =============================================================================

def create_worker(worker_type: str) -> BaseExtractionWorker:
    """Erstellt Worker basierend auf Typ."""
    workers = {
        "documents": DocumentWorker,
        "audio": AudioWorker,
        "video": VideoWorker,
        "images": ImageWorker,
        "email": EmailWorker,
        "archive": ArchiveWorker,
        "3d": ThreeDWorker,
        "cad": CadWorker,
        "gis": GisWorker,
        "fonts": FontsWorker
    }

    if worker_type not in workers:
        raise ValueError(f"Unknown worker type: {worker_type}")

    return workers[worker_type]()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Worker starten."""
    worker = create_worker(WORKER_TYPE)
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
