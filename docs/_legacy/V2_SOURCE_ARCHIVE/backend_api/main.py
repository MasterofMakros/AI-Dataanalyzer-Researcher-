"""
Conductor API - The Brain of the Hybrid AI System
FastAPI backend for job orchestration, worker management, and dashboard data.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import redis
import os
import json
import logging
import uuid
from datetime import datetime

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("conductor")

app = FastAPI(
    title="Conductor API",
    version="2.0.0",
    description="Hybrid AI Orchestration System"
)

# CORS for Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except redis.ConnectionError:
    logger.error("Could not connect to Redis!")
    r = None


# ============ MODELS ============

class Job(BaseModel):
    id: Optional[str] = None
    type: str  # "transcribe", "embed", "summarize"
    payload: dict  # {"path": "F:/...", ...}
    priority: int = 1  # 1-5=Batch, 6-10=Interactive

class JobResponse(BaseModel):
    id: str
    status: str
    position: Optional[int] = None

class WorkerDetail(BaseModel):
    hostname: str
    status: str
    active_job: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_used_mb: Optional[int] = None
    memory_total_mb: Optional[int] = None

class WorkerCommand(BaseModel):
    command: str  # "start", "pause", "stop", "resume"
    
class ComponentStatus(BaseModel):
    name: str
    status: str
    cpu: Optional[float] = None
    memory: Optional[int] = None

class SystemStatus(BaseModel):
    worker: str
    queue_depth: dict
    components: List[ComponentStatus]
    jobs: List[dict]


# ============ ROUTES ============

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "Conductor API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    redis_ok = False
    if r:
        try:
            r.ping()
            redis_ok = True
        except:
            pass
    
    return {
        "status": "healthy" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
    }


# ============ WORKER MANAGEMENT ============

@app.post("/worker/heartbeat")
def worker_heartbeat(detail: WorkerDetail):
    """Called by Worker every ~5 seconds."""
    if not r:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    key = f"worker:{detail.hostname}"
    r.set(key, detail.model_dump_json(), ex=15)
    r.set("system:worker_status", detail.status)
    
    # Check for pending commands
    cmd = r.get(f"worker:{detail.hostname}:command")
    if cmd:
        r.delete(f"worker:{detail.hostname}:command")
        return {"command": cmd}
    
    return {"command": "continue"}


@app.post("/worker/command")
def send_worker_command(cmd: WorkerCommand):
    """Send command to worker."""
    if not r:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    # Get active workers
    workers = r.keys("worker:*")
    workers = [w for w in workers if not w.endswith(":command")]
    
    if not workers:
        return {"status": "no_workers", "message": "No active workers found"}
    
    # Send to first worker (TODO: support multiple)
    worker_key = workers[0]
    r.set(f"{worker_key}:command", cmd.command, ex=30)
    
    logger.info(f"Command '{cmd.command}' sent to {worker_key}")
    return {"status": "sent", "worker": worker_key, "command": cmd.command}


@app.get("/worker/list")
def list_workers():
    """List all registered workers."""
    if not r:
        return {"workers": []}
    
    workers = []
    for key in r.keys("worker:*"):
        if key.endswith(":command"):
            continue
        data = r.get(key)
        if data:
            try:
                workers.append(json.loads(data))
            except:
                pass
    
    return {"workers": workers}


# ============ JOB MANAGEMENT ============

@app.post("/job/submit", response_model=JobResponse)
def submit_job(job: Job):
    """Submit a job to the queue."""
    if not r:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    # Generate ID if not provided
    if not job.id:
        job.id = f"job-{uuid.uuid4().hex[:8]}"
    
    queue_name = "queue:interactive" if job.priority > 5 else "queue:batch"
    job_key = f"job:{job.id}"
    
    # Idempotency check
    if r.exists(job_key):
        existing = r.get(job_key)
        if existing:
            data = json.loads(existing)
            return JobResponse(id=job.id, status=data.get("status", "exists"))
    
    # Store job metadata
    job_data = {
        "id": job.id,
        "type": job.type,
        "payload": job.payload,
        "priority": job.priority,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "estimated_ms": _estimate_job_time(job.type),
    }
    r.set(job_key, json.dumps(job_data), ex=86400)
    
    # Add to queue
    r.lpush(queue_name, json.dumps(job_data))
    position = r.llen(queue_name)
    
    logger.info(f"Job {job.id} [{job.type}] added to {queue_name}")
    return JobResponse(id=job.id, status="queued", position=position)


@app.get("/job/{job_id}")
def get_job_status(job_id: str):
    """Get job status by ID."""
    if not r:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    job_data = r.get(f"job:{job_id}")
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return json.loads(job_data)


@app.get("/job/list/recent")
def list_recent_jobs(limit: int = 20):
    """List recent jobs."""
    if not r:
        return {"jobs": []}
    
    jobs = []
    for key in r.keys("job:*")[:limit]:
        data = r.get(key)
        if data:
            try:
                jobs.append(json.loads(data))
            except:
                pass
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"jobs": jobs[:limit]}


@app.delete("/queue/clear")
def clear_queue(queue: str = "batch"):
    """Clear a job queue."""
    if not r:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    queue_name = f"queue:{queue}"
    count = r.llen(queue_name)
    r.delete(queue_name)
    
    logger.info(f"Queue {queue_name} cleared ({count} jobs)")
    return {"status": "cleared", "queue": queue, "jobs_removed": count}


# ============ SYSTEM STATUS ============

@app.get("/status/system")
def get_system_status():
    """Full system status for dashboard."""
    if not r:
        return {
            "worker": "OFFLINE",
            "queue_depth": {"interactive": 0, "batch": 0},
            "components": [],
            "jobs": [],
        }
    
    worker_status = r.get("system:worker_status") or "OFFLINE"
    interactive_depth = r.llen("queue:interactive")
    batch_depth = r.llen("queue:batch")
    
    # Get component statuses
    components = [
        {"name": "Redis (State)", "status": "online", "cpu": 2, "memory": 45},
        {"name": "API (Brain)", "status": "online", "cpu": 5, "memory": 80},
    ]
    
    # Add worker if online
    worker_data = None
    for key in r.keys("worker:*"):
        if not key.endswith(":command"):
            data = r.get(key)
            if data:
                try:
                    worker_data = json.loads(data)
                except:
                    pass
                break
    
    if worker_data:
        components.append({
            "name": f"Worker ({worker_data.get('hostname', 'Unknown')})",
            "status": "online" if worker_status != "OFFLINE" else "offline",
            "cpu": worker_data.get("cpu_percent", 0),
            "memory": worker_data.get("memory_used_mb", 0),
        })
    else:
        components.append({"name": "Worker (RTX)", "status": "offline", "cpu": 0, "memory": 0})
    
    # Get recent jobs
    jobs = []
    for key in r.keys("job:*")[:10]:
        data = r.get(key)
        if data:
            try:
                jobs.append(json.loads(data))
            except:
                pass
    
    return {
        "worker": worker_status,
        "queue_depth": {
            "interactive": interactive_depth,
            "batch": batch_depth
        },
        "components": components,
        "jobs": jobs,
    }


# ============ HELPERS ============

def _estimate_job_time(job_type: str) -> int:
    """Estimate job duration in milliseconds."""
    estimates = {
        "transcribe": 120000,  # 2 minutes
        "embed": 30000,        # 30 seconds
        "summarize": 60000,    # 1 minute
    }
    return estimates.get(job_type, 60000)
