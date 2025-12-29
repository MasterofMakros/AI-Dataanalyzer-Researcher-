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


# =============================================================================
# BASE WORKER
# =============================================================================

class BaseExtractionWorker(ABC):
    """Basisklasse für alle Extraction Workers."""

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
                        self.logger.error(f"Error processing {job.filename}: {e}")
                        await self.queue_manager.move_to_dlq(self.dlq, job, str(e))
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

    async def _copy_to_local(self, source_path: str) -> Path:
        """Kopiert Datei in lokales temp-Verzeichnis."""
        source = Path(source_path)
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
            return await self._extract_surya(job, local_path)
        except Exception as e:
            self.logger.warning(f"Surya OCR failed: {e}")
            # No fallback - Tesseract deprecated
            raise

    async def _extract_surya(self, job: FileJob, local_path: Path) -> ExtractionResult:
        """Surya OCR via Document Processor (97.7% Accuracy)."""
        with open(local_path, "rb") as f:
            files = {"file": (job.filename, f)}
            response = await self.http_client.post(
                f"{DOCUMENT_PROCESSOR_URL}/process/ocr",
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

        # 1. Audio-Track extrahieren
        audio_path = local_path.with_suffix(".wav")

        subprocess.run([
            "docker", "exec", "conductor-ffmpeg",
            "ffmpeg", "-i", str(local_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            str(audio_path)
        ], capture_output=True, timeout=300)

        # 2. Video-Metadaten extrahieren
        metadata_result = subprocess.run([
            "docker", "exec", "conductor-ffmpeg",
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
    """Verarbeitet E-Mails via Parser Service."""

    def __init__(self):
        super().__init__(
            input_queue="extract:email",
            output_queue="enrich:ner",
            dlq="dlq:extract",
            worker_name=f"email-worker-{CONSUMER_NAME}"
        )

    async def extract(self, job: FileJob, local_path: Path) -> ExtractionResult:
        with open(local_path, "rb") as f:
            files = {"file": (job.filename, f)}
            response = await self.http_client.post(
                f"{PARSER_URL}/parse/email",
                files=files
            )

        if response.status_code != 200:
            raise Exception(f"Parser error: {response.status_code}")

        result = response.json()

        # E-Mail-Struktur in Text konvertieren
        text_parts = []
        if result.get("subject"):
            text_parts.append(f"Betreff: {result['subject']}")
        if result.get("from"):
            text_parts.append(f"Von: {result['from']}")
        if result.get("to"):
            text_parts.append(f"An: {result['to']}")
        if result.get("date"):
            text_parts.append(f"Datum: {result['date']}")
        text_parts.append("")
        if result.get("body"):
            text_parts.append(result["body"])

        text = "\n".join(text_parts)

        return ExtractionResult(
            job_id=job.id,
            file_path=job.path,
            filename=job.filename,
            text=text,
            metadata={
                "subject": result.get("subject"),
                "from": result.get("from"),
                "to": result.get("to"),
                "date": result.get("date"),
                "attachments": result.get("attachments", [])
            },
            entities={
                "emails": [result.get("from"), result.get("to")] if result.get("from") else []
            },
            extraction_method="email-parser",
            confidence=1.0
        )


# =============================================================================
# ARCHIVE WORKER (ZIP, RAR, 7Z)
# =============================================================================

class ArchiveWorker(BaseExtractionWorker):
    """Verarbeitet Archive via 7-Zip (ohne Entpacken)."""

    def __init__(self):
        super().__init__(
            input_queue="extract:archive",
            output_queue="enrich:ner",
            dlq="dlq:extract",
            worker_name=f"archive-worker-{CONSUMER_NAME}"
        )

    async def extract(self, job: FileJob, local_path: Path) -> ExtractionResult:
        import subprocess

        # Archiv-Inhalt listen ohne zu entpacken
        result = subprocess.run([
            "docker", "exec", "conductor-7zip",
            "7z", "l", str(local_path)
        ], capture_output=True, text=True, timeout=60)

        listing = result.stdout

        # Dateiliste parsen
        files = []
        for line in listing.split("\n"):
            if "..." in line or line.strip().startswith("Date"):
                continue
            parts = line.split()
            if len(parts) >= 6:
                filename = " ".join(parts[5:])
                if filename and not filename.startswith("-"):
                    files.append(filename)

        text = f"Archiv: {job.filename}\n"
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
                "file_count": len(files),
                "files": files[:100]
            },
            extraction_method="7zip-listing",
            confidence=1.0
        )


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
        "archive": ArchiveWorker
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
