"""
Neural Vault Orchestrator
=========================

Intelligence-Grade Job Distribution mit Priority Queues.

Implementiert:
- Triage (Priority Scoring)
- Queue-basierte Job-Verteilung
- Dual-Path Processing (Fast/Deep)
- Dead Letter Queue für Fehler
"""

import os
import json
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Queue Names
QUEUES = {
    "intake": {
        "priority": "intake:priority",    # < 1 min processing
        "normal": "intake:normal",        # < 1 hour
        "bulk": "intake:bulk"             # Background
    },
    "extract": {
        "documents": "extract:documents",
        "audio": "extract:audio",
        "video": "extract:video",
        "images": "extract:images",
        "email": "extract:email",
        "archive": "extract:archive",
        "databases": "extract:databases"
    },
    "enrich": {
        "ner": "enrich:ner",
        "classify": "enrich:classify",
        "embed": "enrich:embed"
    },
    "index": {
        "fulltext": "index:fulltext",
        "vector": "index:vector"
    },
    "dlq": {
        "extract": "dlq:extract",
        "enrich": "dlq:enrich",
        "index": "dlq:index"
    }
}


# =============================================================================
# PRIORITY SCORING
# =============================================================================

class Priority(int, Enum):
    CRITICAL = 100   # Sofort verarbeiten
    HIGH = 75        # Innerhalb 1 Minute
    NORMAL = 50      # Innerhalb 1 Stunde
    LOW = 25         # Background
    BULK = 0         # Wenn Kapazität frei


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
    processing_path: str = "fast"  # fast oder deep
    status: str = "pending"
    retries: int = 0
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "FileJob":
        return cls(**data)


def calculate_priority(file_path: str, file_size: int, modified: datetime) -> tuple[int, str]:
    """
    Intelligence-Grade Triage: Berechnet Priority Score und Processing Path.

    Returns:
        (priority_score, processing_path)
    """
    score = 50
    path = "fast"
    filename = Path(file_path).name.lower()
    ext = Path(file_path).suffix.lower().lstrip(".")

    # ══════════════════════════════════════════════════════════════════════════
    # RECENCY BOOST
    # ══════════════════════════════════════════════════════════════════════════
    age = datetime.now() - modified
    if age < timedelta(hours=1):
        score += 30
    elif age < timedelta(days=1):
        score += 20
    elif age < timedelta(weeks=1):
        score += 10

    # ══════════════════════════════════════════════════════════════════════════
    # FILE TYPE WEIGHT
    # ══════════════════════════════════════════════════════════════════════════
    type_weights = {
        # Kommunikation (höchste Priorität)
        "eml": 25, "msg": 25,
        # Dokumente
        "pdf": 15, "docx": 15, "doc": 15,
        "xlsx": 12, "xls": 12, "csv": 10,
        # Text
        "txt": 8, "md": 8, "json": 8,
        # Audio (kann Gespräche sein)
        "mp3": 12, "wav": 12, "m4a": 12, "flac": 10,
        # Video
        "mp4": 8, "mkv": 8, "avi": 8, "mov": 8,
        # Bilder
        "jpg": 5, "jpeg": 5, "png": 5, "tiff": 5,
        # Archive
        "zip": 3, "rar": 3, "7z": 3,
    }
    score += type_weights.get(ext, 0)

    # ══════════════════════════════════════════════════════════════════════════
    # KEYWORD BOOST (wichtige Begriffe im Dateinamen)
    # ══════════════════════════════════════════════════════════════════════════
    priority_keywords = [
        "vertrag", "contract", "rechnung", "invoice", "beleg",
        "passwort", "password", "geheim", "secret", "confidential",
        "steuer", "tax", "bank", "konto", "account",
        "wichtig", "urgent", "dringend", "asap",
        "bewerbung", "application", "zeugnis", "certificate"
    ]
    for keyword in priority_keywords:
        if keyword in filename:
            score += 15
            break

    # ══════════════════════════════════════════════════════════════════════════
    # SIZE-BASED ROUTING
    # ══════════════════════════════════════════════════════════════════════════
    size_mb = file_size / (1024 * 1024)

    # Große Dateien: Deep Path (Background)
    if size_mb > 50:
        path = "deep"
        if score < 70:
            score -= 10  # Große unwichtige Dateien nach hinten

    # Sehr große Dateien: Bulk Queue
    if size_mb > 500:
        score = max(score - 20, 0)

    # ══════════════════════════════════════════════════════════════════════════
    # COMPLEXITY-BASED ROUTING
    # ══════════════════════════════════════════════════════════════════════════
    # Dateitypen die Deep Processing brauchen
    deep_types = ["pdf", "mp3", "wav", "m4a", "mp4", "mkv", "avi"]
    if ext in deep_types and size_mb > 10:
        path = "deep"

    return min(100, max(0, score)), path


def get_queue_for_type(extension: str) -> str:
    """Bestimmt die richtige Extraction Queue basierend auf Dateityp."""
    ext = extension.lower().lstrip(".")

    type_to_queue = {
        # Documents
        "pdf": "extract:documents",
        "docx": "extract:documents",
        "doc": "extract:documents",
        "xlsx": "extract:documents",
        "xls": "extract:documents",
        "pptx": "extract:documents",
        "txt": "extract:documents",
        "rtf": "extract:documents",
        "html": "extract:documents",
        "csv": "extract:documents",

        # Audio
        "mp3": "extract:audio",
        "wav": "extract:audio",
        "m4a": "extract:audio",
        "flac": "extract:audio",
        "aac": "extract:audio",
        "ogg": "extract:audio",

        # Video
        "mp4": "extract:video",
        "mkv": "extract:video",
        "avi": "extract:video",
        "mov": "extract:video",
        "wmv": "extract:video",
        "webm": "extract:video",

        # Images
        "jpg": "extract:images",
        "jpeg": "extract:images",
        "png": "extract:images",
        "tiff": "extract:images",
        "bmp": "extract:images",
        "webp": "extract:images",

        # Email
        "eml": "extract:email",
        "msg": "extract:email",

        # Archive
        "zip": "extract:archive",
        "rar": "extract:archive",
        "7z": "extract:archive",
        "tar": "extract:archive",
        "gz": "extract:archive",

        # Databases
        "mdb": "extract:databases",
        "accdb": "extract:databases",
        "dbf": "extract:databases",
        "sqlite": "extract:databases",
        "sqlite3": "extract:databases",
        "db": "extract:databases",
        "db3": "extract:databases",
    }

    return type_to_queue.get(ext, "extract:documents")


# =============================================================================
# REDIS CLIENT
# =============================================================================

class QueueManager:
    """Verwaltet Redis Streams für Job Queues."""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Verbindung zu Redis herstellen."""
        self.redis = await redis.from_url(
            REDIS_URL,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True
        )
        logger.info("Connected to Redis")

    async def disconnect(self):
        """Verbindung trennen."""
        if self.redis:
            await self.redis.close()

    async def enqueue(self, queue: str, job: FileJob) -> str:
        """Job in Queue einfügen."""
        message_id = await self.redis.xadd(
            queue,
            {"data": json.dumps(job.to_dict())},
            maxlen=10000  # Queue-Größe begrenzen
        )
        logger.info(f"Enqueued job {job.id} to {queue} with priority {job.priority}")
        return message_id

    async def dequeue(self, queue: str, consumer_group: str, consumer: str, count: int = 1) -> List[FileJob]:
        """Jobs aus Queue holen."""
        try:
            # Consumer Group erstellen falls nicht existiert
            try:
                await self.redis.xgroup_create(queue, consumer_group, id="0", mkstream=True)
            except redis.ResponseError:
                pass  # Gruppe existiert bereits

            # Jobs lesen
            messages = await self.redis.xreadgroup(
                consumer_group,
                consumer,
                {queue: ">"},
                count=count,
                block=5000  # 5 Sekunden warten
            )

            jobs = []
            for stream, entries in messages:
                for entry_id, data in entries:
                    job = FileJob.from_dict(json.loads(data["data"]))
                    job.id = entry_id  # Redis ID übernehmen
                    jobs.append(job)

            return jobs

        except Exception as e:
            logger.error(f"Dequeue error: {e}")
            return []

    async def ack(self, queue: str, consumer_group: str, message_id: str):
        """Job als verarbeitet markieren."""
        await self.redis.xack(queue, consumer_group, message_id)

    async def move_to_dlq(self, source_queue: str, dlq: str, job: FileJob, error: str):
        """Job in Dead Letter Queue verschieben."""
        job.status = "failed"
        job.error = error
        job.retries += 1
        await self.enqueue(dlq, job)
        logger.warning(f"Moved job {job.id} to DLQ: {error}")

    async def get_queue_stats(self) -> Dict[str, int]:
        """Statistiken aller Queues."""
        stats = {}
        for category, queues in QUEUES.items():
            if isinstance(queues, dict):
                for name, queue in queues.items():
                    try:
                        info = await self.redis.xinfo_stream(queue)
                        stats[queue] = info.get("length", 0)
                    except redis.ResponseError:
                        stats[queue] = 0
        return stats


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Neural Vault Orchestrator",
    description="Intelligence-Grade Job Distribution",
    version="1.0.0"
)

queue_manager = QueueManager()


class SubmitJobRequest(BaseModel):
    path: str
    filename: Optional[str] = None
    size: Optional[int] = None
    modified: Optional[str] = None
    force_deep: bool = False


class JobResponse(BaseModel):
    job_id: str
    queue: str
    priority: int
    processing_path: str


@app.on_event("startup")
async def startup():
    await queue_manager.connect()


@app.on_event("shutdown")
async def shutdown():
    await queue_manager.disconnect()


@app.get("/health")
async def health():
    """Health Check."""
    try:
        await queue_manager.redis.ping()
        return {"status": "healthy", "redis": True}
    except Exception:
        return {"status": "unhealthy", "redis": False}


@app.post("/submit", response_model=JobResponse)
async def submit_job(request: SubmitJobRequest):
    """
    Job zur Verarbeitung einreichen.

    Berechnet automatisch Priority und wählt Processing Path.
    """
    file_path = Path(request.path)

    # Metadaten sammeln
    if request.size is None:
        try:
            request.size = file_path.stat().st_size
        except Exception:
            request.size = 0

    if request.modified is None:
        try:
            request.modified = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        except Exception:
            request.modified = datetime.now().isoformat()

    # Priority und Path berechnen
    modified_dt = datetime.fromisoformat(request.modified)
    priority, processing_path = calculate_priority(
        str(file_path),
        request.size,
        modified_dt
    )

    # Force Deep Path wenn angefordert
    if request.force_deep:
        processing_path = "deep"

    # Job erstellen
    job = FileJob(
        id=hashlib.sha256(str(file_path).encode()).hexdigest()[:16],
        path=str(file_path),
        filename=request.filename or file_path.name,
        extension=file_path.suffix.lower().lstrip("."),
        size=request.size,
        modified=request.modified,
        priority=priority,
        processing_path=processing_path
    )

    # Queue basierend auf Priority wählen
    if priority >= 75:
        intake_queue = QUEUES["intake"]["priority"]
    elif priority >= 40:
        intake_queue = QUEUES["intake"]["normal"]
    else:
        intake_queue = QUEUES["intake"]["bulk"]

    # In Queue einfügen
    message_id = await queue_manager.enqueue(intake_queue, job)

    return JobResponse(
        job_id=message_id,
        queue=intake_queue,
        priority=priority,
        processing_path=processing_path
    )


@app.post("/submit/batch")
async def submit_batch(paths: List[str]):
    """Mehrere Jobs auf einmal einreichen."""
    results = []
    for path in paths:
        try:
            result = await submit_job(SubmitJobRequest(path=path))
            results.append({"path": path, "status": "queued", **result.dict()})
        except Exception as e:
            results.append({"path": path, "status": "error", "error": str(e)})
    return {"submitted": len([r for r in results if r["status"] == "queued"]), "results": results}


@app.get("/stats")
async def get_stats():
    """Queue-Statistiken."""
    stats = await queue_manager.get_queue_stats()
    return {
        "queues": stats,
        "total_pending": sum(stats.values())
    }


@app.get("/queues")
async def list_queues():
    """Alle verfügbaren Queues."""
    return QUEUES


@app.post("/route/{job_id}")
async def route_job(job_id: str, target_queue: str):
    """Job manuell in andere Queue verschieben."""
    # TODO: Implementierung für manuelle Umleitung
    return {"status": "not_implemented"}


# =============================================================================
# WORKER BASE CLASS
# =============================================================================

class BaseWorker:
    """
    Basisklasse für alle Processing Workers.

    Jeder Worker:
    1. Liest aus einer Input Queue
    2. Verarbeitet den Job
    3. Schreibt in eine Output Queue (oder mehrere)
    4. Bei Fehler: Dead Letter Queue
    """

    def __init__(
        self,
        input_queue: str,
        output_queues: List[str],
        dlq: str,
        consumer_group: str,
        consumer_name: str
    ):
        self.input_queue = input_queue
        self.output_queues = output_queues
        self.dlq = dlq
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.queue_manager = QueueManager()
        self.running = False

    async def start(self):
        """Worker starten."""
        await self.queue_manager.connect()
        self.running = True
        logger.info(f"Worker {self.consumer_name} started, listening on {self.input_queue}")

        while self.running:
            try:
                jobs = await self.queue_manager.dequeue(
                    self.input_queue,
                    self.consumer_group,
                    self.consumer_name,
                    count=1
                )

                for job in jobs:
                    try:
                        # Job verarbeiten
                        result = await self.process(job)

                        # In Output Queues schreiben
                        for output_queue in self.output_queues:
                            await self.queue_manager.enqueue(output_queue, result)

                        # Als verarbeitet markieren
                        await self.queue_manager.ack(
                            self.input_queue,
                            self.consumer_group,
                            job.id
                        )

                        logger.info(f"Processed job {job.id}")

                    except Exception as e:
                        logger.error(f"Processing error for {job.id}: {e}")
                        await self.queue_manager.move_to_dlq(
                            self.input_queue,
                            self.dlq,
                            job,
                            str(e)
                        )

            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        """Worker stoppen."""
        self.running = False
        await self.queue_manager.disconnect()

    async def process(self, job: FileJob) -> FileJob:
        """
        Job verarbeiten - muss von Subklassen implementiert werden.

        Args:
            job: Der zu verarbeitende Job

        Returns:
            Der verarbeitete Job (mit aktualisierten Feldern)
        """
        raise NotImplementedError("Subclasses must implement process()")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020)
