"""
Neural Search API - RAG Search with LLM Synthesis and Streaming
================================================================
Provides intelligent search over indexed documents with:
- Semantic search via Qdrant
- LLM synthesis with inline citations (Ollama)
- Real-time streaming responses (SSE)
- Pipeline status monitoring
"""

import os
import json
import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Optional, List, AsyncGenerator
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# =============================================================================
# Configuration
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neural-search")

# Environment Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "neural_vault")

# Search Configuration
MAX_SOURCES = int(os.getenv("MAX_SOURCES", "8"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.5"))


# =============================================================================
# Pydantic Models
# =============================================================================

class TranscriptLine(BaseModel):
    timestamp: str
    speaker: str
    text: str
    isHighlighted: bool = False


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Source(BaseModel):
    id: str
    type: str  # pdf, audio, image, email, video, text
    filename: str
    path: str
    folder: Optional[str] = None
    fileExtension: Optional[str] = None
    fileCreated: Optional[str] = None
    fileModified: Optional[str] = None
    tags: List[str] = []
    confidence: float
    excerpt: str
    highlightedText: Optional[str] = None
    page: Optional[int] = None
    line: Optional[str] = None
    timestamp: Optional[str] = None
    duration: Optional[str] = None
    speakers: Optional[List[str]] = None
    transcript: Optional[List[TranscriptLine]] = None
    extractedVia: str = "Tika"
    boundingBox: Optional[BoundingBox] = None


class Citation(BaseModel):
    index: int
    sourceId: str
    text: str


class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=8, ge=1, le=20)
    filters: Optional[dict] = None


class SearchResponse(BaseModel):
    id: str
    query: str
    answer: str
    citations: List[Citation]
    sources: List[Source]
    timestamp: datetime
    processingTimeMs: int


class FollowUpQuestion(BaseModel):
    id: str
    icon: str
    question: str


class PipelineStatus(BaseModel):
    gpuStatus: str  # online, offline, busy
    gpuModel: str
    vramUsage: float
    workersActive: int
    workersTotal: int
    queueDepth: int
    indexedDocuments: int
    lastSync: datetime


class SearchProgress(BaseModel):
    step: str  # analyzing, searching, reading, synthesizing, complete
    progress: int
    keywords: Optional[List[str]] = None
    documentsFound: Optional[int] = None
    documentsTotal: Optional[int] = None
    currentSource: Optional[str] = None
    sourcesRead: Optional[int] = None
    sourcesTotal: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict


# =============================================================================
# Global State & Connections
# =============================================================================

redis_client: Optional[redis.Redis] = None
http_client: Optional[httpx.AsyncClient] = None

# Active search sessions for progress tracking
active_searches: dict[str, SearchProgress] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global redis_client, http_client

    # Startup
    logger.info("Starting Neural Search API...")

    # Initialize Redis
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD or None,
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✓ Redis connected")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        redis_client = None

    # Initialize HTTP client for Ollama
    http_client = httpx.AsyncClient(timeout=120.0)
    logger.info("✓ HTTP client initialized")

    logger.info("Neural Search API ready!")

    yield

    # Shutdown
    logger.info("Shutting down Neural Search API...")
    if redis_client:
        await redis_client.close()
    if http_client:
        await http_client.aclose()


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Neural Search API",
    description="RAG Search with LLM Synthesis and Streaming",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Helper Functions
# =============================================================================

def generate_search_id() -> str:
    """Generate unique search ID."""
    return hashlib.sha256(f"{datetime.now().isoformat()}".encode()).hexdigest()[:16]


def extract_keywords(query: str) -> List[str]:
    """Extract keywords from query for display."""
    # Simple keyword extraction - could be enhanced with NLP
    stopwords = {'was', 'weiß', 'ich', 'über', 'meinen', 'meine', 'der', 'die', 'das',
                 'ein', 'eine', 'und', 'oder', 'ist', 'sind', 'hat', 'haben', 'wie',
                 'wo', 'wann', 'warum', 'welche', 'welcher', 'welches', 'mir', 'zeige'}
    words = query.lower().replace('?', '').replace('!', '').split()
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return keywords[:6]  # Max 6 keywords


def detect_source_type(filename: str, metadata: dict) -> str:
    """Detect source type from filename and metadata."""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''

    type_map = {
        'pdf': 'pdf',
        'doc': 'pdf', 'docx': 'pdf',
        'mp3': 'audio', 'wav': 'audio', 'm4a': 'audio', 'ogg': 'audio',
        'mp4': 'video', 'mkv': 'video', 'avi': 'video', 'mov': 'video',
        'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 'webp': 'image',
        'eml': 'email', 'msg': 'email',
        'txt': 'text', 'md': 'text', 'json': 'text', 'xml': 'text',
    }

    return type_map.get(ext, 'text')


def detect_extractor(metadata: dict) -> str:
    """Detect which extractor was used."""
    extractor = metadata.get('extractor', metadata.get('extracted_via', ''))
    if 'docling' in extractor.lower():
        return 'Docling'
    if 'surya' in extractor.lower():
        return 'Surya'
    if 'whisper' in extractor.lower():
        return 'WhisperX'
    return 'Tika'


def convert_hit_to_source(hit: dict, index: int) -> Source:
    """Convert Qdrant payload hit to Source object."""
    payload = hit.get('payload', hit)
    metadata = payload.get('metadata', payload)
    filename = payload.get('filename', payload.get('title', f'Document {index + 1}'))
    file_path = payload.get('path', payload.get('file_path', ''))

    # Calculate confidence from payload or position
    confidence = payload.get('confidence')
    if confidence is None:
        confidence = min(99, max(70, 100 - (index * 3)))

    source_type = detect_source_type(filename, metadata)

    source = Source(
        id=str(hit.get('id', payload.get('id', str(index)))),
        type=source_type,
        filename=filename,
        path=file_path,
        folder=str(os.path.dirname(file_path)) if file_path else None,
        fileExtension=payload.get('extension') or os.path.splitext(filename)[1].lower(),
        fileCreated=payload.get('file_created'),
        fileModified=payload.get('file_modified'),
        tags=payload.get('tags', []) or [],
        confidence=confidence,
        excerpt=payload.get('content', payload.get('text', ''))[:500],
        extractedVia=detect_extractor(metadata),
    )

    # Add type-specific fields
    if source_type == 'pdf':
        source.page = metadata.get('page', metadata.get('page_number'))
        source.line = metadata.get('line', metadata.get('line_range'))
        source.highlightedText = hit.get('_formatted', {}).get('content', '')[:300]

    elif source_type == 'audio':
        source.timestamp = metadata.get('timestamp', metadata.get('start_time'))
        source.duration = metadata.get('duration')
        source.speakers = metadata.get('speakers', [])
        # Add transcript if available
        if 'transcript' in metadata:
            source.transcript = [
                TranscriptLine(
                    timestamp=t.get('timestamp', '00:00'),
                    speaker=t.get('speaker', 'Speaker'),
                    text=t.get('text', ''),
                    isHighlighted=t.get('highlighted', False)
                )
                for t in metadata['transcript'][:10]  # Limit to 10 lines
            ]

    elif source_type == 'image':
        if 'bounding_box' in metadata:
            bb = metadata['bounding_box']
            source.boundingBox = BoundingBox(
                x=bb.get('x', 0),
                y=bb.get('y', 0),
                width=bb.get('width', 100),
                height=bb.get('height', 20)
            )

    return source


async def search_qdrant(query: str, limit: int = 8) -> List[dict]:
    """Search documents in Qdrant (baseline scroll fallback)."""
    try:
        response = await http_client.post(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/scroll",
            json={
                "limit": limit,
                "with_payload": True,
                "with_vector": False
            },
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("result", {}).get("points", [])
        logger.warning(f"Qdrant search failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Qdrant search failed: {e}")
    return []


async def generate_llm_response(
    query: str,
    sources: List[Source],
    stream: bool = True
) -> AsyncGenerator[str, None]:
    """Generate LLM response with citations using Ollama."""

    # Build context from sources
    context_parts = []
    for i, source in enumerate(sources, 1):
        context_parts.append(f"[Quelle {i}] ({source.filename}):\n{source.excerpt}\n")

    context = "\n".join(context_parts)

    # Build prompt
    system_prompt = """Du bist ein hilfreicher Assistent, der Fragen basierend auf den bereitgestellten Quellen beantwortet.

WICHTIGE REGELN:
1. Antworte AUF DEUTSCH
2. Verwende Superscript-Ziffern (¹, ², ³, etc.) als Quellenverweise DIREKT nach relevanten Aussagen
3. Formatiere wichtige Begriffe mit **fett**
4. Sei präzise und direkt
5. Wenn eine Information aus mehreren Quellen stammt, zitiere alle relevanten Quellen

Beispiel: "Der Vertrag läuft seit **15. März 2022** ¹ mit einer monatlichen Gebühr von **39,99€** ¹²."
"""

    user_prompt = f"""Basierend auf den folgenden Quellen, beantworte die Frage.

QUELLEN:
{context}

FRAGE: {query}

ANTWORT (mit Quellenverweisen ¹²³):"""

    try:
        if stream:
            # Streaming response
            async with http_client.stream(
                'POST',
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": user_prompt,
                    "system": system_prompt,
                    "stream": True,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                    }
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'response' in data:
                                yield data['response']
                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
        else:
            # Non-streaming response
            response = await http_client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": user_prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                    }
                }
            )
            data = response.json()
            yield data.get('response', 'Keine Antwort generiert.')

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        yield f"Fehler bei der Antwortgenerierung: {str(e)}"


def extract_citations(answer: str, sources: List[Source]) -> List[Citation]:
    """Extract citations from answer text."""
    citations = []
    superscripts = '¹²³⁴⁵⁶⁷⁸⁹'

    for i, char in enumerate(superscripts):
        if char in answer and i < len(sources):
            citations.append(Citation(
                index=i + 1,
                sourceId=sources[i].id,
                text=sources[i].excerpt[:100]
            ))

    return citations


async def generate_follow_ups(query: str, answer: str, sources: List[Source]) -> List[FollowUpQuestion]:
    """Generate follow-up questions based on the search context."""
    # Extract entities and topics from sources
    topics = set()
    for source in sources:
        # Simple extraction of potential topics
        words = source.excerpt.split()
        for word in words:
            if len(word) > 5 and word[0].isupper():
                topics.add(word.strip('.,!?'))

    # Generate contextual follow-ups
    icons = ['📅', '💰', '🎫', '📊', '🔍', '📋']
    follow_ups = []

    # Template-based follow-ups
    templates = [
        ("📅", "Wann wurde {} zuletzt aktualisiert?"),
        ("💰", "Wie hoch sind die Gesamtkosten für {}?"),
        ("📊", "Zeige mir eine Zusammenfassung von {}"),
        ("🔍", "Was sind ähnliche Dokumente zu {}?"),
    ]

    topic_list = list(topics)[:4]
    for i, (icon, template) in enumerate(templates[:len(topic_list)]):
        follow_ups.append(FollowUpQuestion(
            id=f"followup_{i}",
            icon=icon,
            question=template.format(topic_list[i] if i < len(topic_list) else "diesem Thema")
        ))

    return follow_ups[:4]


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    services = {
        "redis": "connected" if redis_client else "disconnected",
        "qdrant": "unknown",
        "ollama": "unknown"  # Checked on demand
    }

    # Check Ollama
    try:
        response = await http_client.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
        services["ollama"] = "connected" if response.status_code == 200 else "error"
    except:
        services["ollama"] = "disconnected"

    try:
        response = await http_client.get(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}", timeout=5.0)
        services["qdrant"] = "connected" if response.status_code == 200 else "error"
    except Exception:
        services["qdrant"] = "disconnected"

    return HealthResponse(
        status="healthy" if all(v == "connected" for v in services.values()) else "degraded",
        version="1.0.0",
        services=services
    )


@app.post("/api/neural-search")
async def neural_search(request: SearchRequest):
    """
    Main neural search endpoint.
    Returns complete search response with LLM-synthesized answer and sources.
    """
    start_time = datetime.now()
    search_id = generate_search_id()

    logger.info(f"[{search_id}] Neural search: {request.query}")

    # Step 1: Search Qdrant
    hits = await search_qdrant(request.query, request.limit)

    if not hits:
        return SearchResponse(
            id=search_id,
            query=request.query,
            answer="Keine relevanten Dokumente gefunden. Bitte versuche eine andere Suchanfrage.",
            citations=[],
            sources=[],
            timestamp=datetime.now(),
            processingTimeMs=int((datetime.now() - start_time).total_seconds() * 1000)
        )

    # Step 2: Convert hits to sources
    sources = [convert_hit_to_source(hit, i) for i, hit in enumerate(hits)]

    # Step 3: Generate LLM response
    answer_parts = []
    async for chunk in generate_llm_response(request.query, sources, stream=False):
        answer_parts.append(chunk)
    answer = "".join(answer_parts)

    # Step 4: Extract citations
    citations = extract_citations(answer, sources)

    processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

    return SearchResponse(
        id=search_id,
        query=request.query,
        answer=answer,
        citations=citations,
        sources=sources,
        timestamp=datetime.now(),
        processingTimeMs=processing_time
    )


@app.post("/api/neural-search/stream")
async def neural_search_stream(request: SearchRequest):
    """
    Streaming neural search endpoint using Server-Sent Events.
    Streams search progress and answer tokens in real-time.
    """
    search_id = generate_search_id()

    async def event_generator():
        start_time = datetime.now()

        # Step 1: Analyzing
        yield {
            "event": "progress",
            "data": json.dumps({
                "step": "analyzing",
                "progress": 10,
                "keywords": extract_keywords(request.query)
            })
        }
        await asyncio.sleep(0.5)

        # Step 2: Searching
        yield {
            "event": "progress",
            "data": json.dumps({
                "step": "searching",
                "progress": 30,
                "keywords": extract_keywords(request.query)
            })
        }

        hits = await search_qdrant(request.query, request.limit)
        total_docs = 0
        try:
            response = await http_client.get(
                f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}",
                timeout=5.0
            )
            if response.status_code == 200:
                stats = response.json().get("result", {})
                total_docs = stats.get("points_count", 0) or stats.get("vectors_count", 0)
        except Exception:
            pass

        yield {
            "event": "progress",
            "data": json.dumps({
                "step": "searching",
                "progress": 50,
                "documentsFound": len(hits),
                "documentsTotal": total_docs
            })
        }

        # Step 3: Reading sources
        sources = [convert_hit_to_source(hit, i) for i, hit in enumerate(hits)]

        for i, source in enumerate(sources):
            yield {
                "event": "progress",
                "data": json.dumps({
                    "step": "reading",
                    "progress": 50 + int((i + 1) / len(sources) * 25),
                    "currentSource": source.filename,
                    "sourcesRead": i + 1,
                    "sourcesTotal": len(sources)
                })
            }
            await asyncio.sleep(0.1)

        # Send sources
        yield {
            "event": "sources",
            "data": json.dumps([s.model_dump() for s in sources])
        }

        # Step 4: Synthesizing
        yield {
            "event": "progress",
            "data": json.dumps({
                "step": "synthesizing",
                "progress": 80
            })
        }

        # Stream LLM response
        full_answer = ""
        async for chunk in generate_llm_response(request.query, sources, stream=True):
            full_answer += chunk
            yield {
                "event": "token",
                "data": chunk
            }

        # Complete
        citations = extract_citations(full_answer, sources)
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        yield {
            "event": "complete",
            "data": json.dumps({
                "id": search_id,
                "query": request.query,
                "answer": full_answer,
                "citations": [c.model_dump() for c in citations],
                "processingTimeMs": processing_time
            })
        }

        # Generate follow-ups
        follow_ups = await generate_follow_ups(request.query, full_answer, sources)
        yield {
            "event": "followups",
            "data": json.dumps([f.model_dump() for f in follow_ups])
        }

    return EventSourceResponse(event_generator())


@app.get("/api/pipeline/status", response_model=PipelineStatus)
async def get_pipeline_status():
    """
    Get aggregated pipeline status from all services.
    """
    status = PipelineStatus(
        gpuStatus="offline",
        gpuModel="Unknown",
        vramUsage=0,
        workersActive=0,
        workersTotal=3,
        queueDepth=0,
        indexedDocuments=0,
        lastSync=datetime.now()
    )

    # Get GPU status from document-processor
    try:
        response = await http_client.get(
            "http://document-processor:8005/health",
            timeout=5.0
        )
        if response.status_code == 200:
            data = response.json()
            if 'gpu' in data:
                status.gpuStatus = "online" if data['gpu'].get('available') else "offline"
                status.gpuModel = data['gpu'].get('name', 'Unknown')
                status.vramUsage = data['gpu'].get('memory_used_percent', 0)
    except Exception as e:
        logger.debug(f"Document processor not available: {e}")

    # Get queue depth from Redis
    if redis_client:
        try:
            # Count items in priority queues
            queues = ['intake:priority', 'intake:normal', 'intake:bulk']
            total_depth = 0
            for queue in queues:
                try:
                    length = await redis_client.xlen(queue)
                    total_depth += length
                except:
                    pass
            status.queueDepth = total_depth
        except Exception as e:
            logger.debug(f"Redis queue check failed: {e}")

    # Get worker status from orchestrator
    try:
        response = await http_client.get(
            "http://orchestrator:8020/stats",
            timeout=5.0
        )
        if response.status_code == 200:
            data = response.json()
            status.workersActive = data.get('active_workers', 0)
            status.workersTotal = data.get('total_workers', 3)
    except Exception as e:
        logger.debug(f"Orchestrator not available: {e}")

    # Get index stats from Qdrant
    try:
        response = await http_client.get(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}",
            timeout=5.0
        )
        if response.status_code == 200:
            stats = response.json().get("result", {})
            status.indexedDocuments = stats.get("points_count", 0) or stats.get("vectors_count", 0)
    except Exception as e:
        logger.debug(f"Qdrant stats failed: {e}")

    return status


@app.post("/api/neural-search/follow-ups")
async def get_follow_ups(request: SearchRequest):
    """Generate follow-up questions for a query."""
    # Simple follow-up generation based on query analysis
    keywords = extract_keywords(request.query)

    templates = [
        ("📅", f"Wann wurde {keywords[0] if keywords else 'dies'} zuletzt aktualisiert?"),
        ("💰", f"Wie hoch waren die Kosten für {keywords[0] if keywords else 'dies'} im Jahr 2024?"),
        ("📊", f"Zeige mir alle Dokumente zu {keywords[0] if keywords else 'diesem Thema'}"),
        ("🔍", f"Was sind verwandte Themen zu {keywords[0] if keywords else 'meiner Suche'}?"),
    ]

    return [
        FollowUpQuestion(id=f"q{i}", icon=icon, question=q)
        for i, (icon, q) in enumerate(templates)
    ]


@app.get("/api/sources/{source_id}")
async def get_source(source_id: str):
    """Get detailed source information."""
    try:
        response = await http_client.get(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/{source_id}",
            timeout=5.0
        )
        if response.status_code == 200:
            data = response.json().get("result")
            if data:
                return convert_hit_to_source(data, 0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail="Source not found")


@app.get("/api/sources/{source_id}/similar")
async def get_similar_sources(source_id: str, limit: int = Query(default=5, ge=1, le=10)):
    """Find sources similar to the given source."""
    try:
        response = await http_client.get(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/{source_id}",
            timeout=5.0
        )
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Source not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return []


# =============================================================================
# Dashboard Compatibility Endpoints (for App.tsx)
# =============================================================================

@app.get("/api/status/system")
async def get_system_status():
    """System status for dashboard compatibility."""
    pipeline = await get_pipeline_status()
    qdrant_status = "offline"
    try:
        response = await http_client.get(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}",
            timeout=5.0
        )
        if response.status_code == 200:
            qdrant_status = "online"
    except Exception:
        pass

    return {
        "worker": "IDLE" if pipeline.gpuStatus == "online" else "OFFLINE",
        "queue_depth": {
            "interactive": 0,
            "batch": pipeline.queueDepth
        },
        "components": [
            {"name": "Redis", "status": "online" if redis_client else "offline"},
            {"name": "Qdrant", "status": qdrant_status},
            {"name": "GPU", "status": pipeline.gpuStatus, "cpu": int(pipeline.vramUsage)},
        ],
        "jobs": []
    }


@app.post("/api/worker/command")
async def worker_command(command: dict):
    """Worker control command (placeholder)."""
    cmd = command.get("command", "status")
    logger.info(f"Worker command: {cmd}")
    return {"status": "ok", "command": cmd}


@app.post("/api/job/submit")
async def submit_job(job: dict):
    """Submit a job (placeholder)."""
    job_id = generate_search_id()
    logger.info(f"Job submitted: {job_id}")
    return {"id": job_id, "status": "queued"}


@app.delete("/api/queue/clear")
async def clear_queue(queue: str = Query(default="batch")):
    """Clear a queue (placeholder)."""
    logger.info(f"Queue clear requested: {queue}")
    return {"jobs_removed": 0}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8040)
