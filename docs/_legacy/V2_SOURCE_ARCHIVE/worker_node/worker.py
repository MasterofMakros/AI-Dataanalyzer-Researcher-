"""
Conductor Worker Node - Cross-Platform Compute Engine
Handles job processing with GameMode detection and real AI integrations.
Supports Windows, Linux, and macOS.
"""
import time
import json
import os
import logging
import socket
import platform

import redis
import psutil

from validate_media import validate_media_file
from insomnia import InsomniaContext
from gamemode import check_gamemode

# Configuration
CONDUCTOR_API_URL = os.getenv("CONDUCTOR_API_URL", "http://192.168.1.254:8000")
REDIS_HOST = os.getenv("REDIS_HOST", "192.168.1.254")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
WORKER_ID = socket.gethostname()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(f"worker.{WORKER_ID}")


class WorkerNode:
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.active = True
        self.current_job = None
        self.paused = False
        self.transcribe_service = None
        self.embed_service = None
        
        logger.info(f"Worker {WORKER_ID} initializing...")
        logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
        
        # Lazy load AI services
        self._init_services()
    
    def _init_services(self):
        """Initialize AI services (transcription, embedding)."""
        try:
            from transcribe import get_transcription_service
            self.transcribe_service = get_transcription_service()
            logger.info("Transcription service loaded")
        except Exception as e:
            logger.warning(f"Transcription service unavailable: {e}")
        
        try:
            from embed import get_embedding_service
            self.embed_service = get_embedding_service()
            logger.info("Embedding service loaded")
        except Exception as e:
            logger.warning(f"Embedding service unavailable: {e}")
    
    def _check_gamemode(self):
        """Check if gaming processes are running (cross-platform)."""
        return check_gamemode()
    
    def send_heartbeat(self, status="IDLE"):
        """Send status to Redis for dashboard."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            payload = {
                "hostname": WORKER_ID,
                "status": status,
                "active_job": self.current_job,
                "cpu_percent": cpu_percent,
                "memory_used_mb": memory.used // (1024 * 1024),
                "memory_total_mb": memory.total // (1024 * 1024),
                "timestamp": time.time(),
            }
            
            self.redis_client.set(f"worker:{WORKER_ID}", json.dumps(payload), ex=15)
            self.redis_client.set("system:worker_status", status)
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
    
    def update_job_status(self, job_id: str, status: str, progress: int = 0, result: dict = None):
        """Update job status in Redis."""
        try:
            job_key = f"job:{job_id}"
            job_data = {
                "status": status,
                "progress": progress,
                "updated_at": time.time(),
            }
            if result:
                job_data["result"] = result
            
            self.redis_client.set(job_key, json.dumps(job_data), ex=86400)  # 24h TTL
        except Exception as e:
            logger.warning(f"Failed to update job status: {e}")
    
    def process_job(self, job_json: str):
        """Execute job based on type."""
        try:
            job = json.loads(job_json)
            job_id = job.get('id', 'unknown')
            job_type = job.get('type', 'unknown')
            file_path = job.get('payload', {}).get('path', '')
            
            self.current_job = job_id
            logger.info(f"Processing Job {job_id} [{job_type}]: {file_path}")
            self.send_heartbeat("BUSY")
            self.update_job_status(job_id, "processing", 10)
            
            result = None
            
            # Route to appropriate handler
            if job_type == "transcribe":
                result = self._handle_transcribe(job_id, file_path)
            elif job_type == "embed":
                result = self._handle_embed(job_id, file_path)
            elif job_type == "summarize":
                result = self._handle_summarize(job_id, file_path)
            else:
                logger.warning(f"Unknown job type: {job_type}")
                result = {"error": f"Unknown job type: {job_type}"}
            
            # Mark completed
            if result and not result.get("error"):
                self.update_job_status(job_id, "done", 100, result)
                logger.info(f"Job {job_id} COMPLETED")
            else:
                self.update_job_status(job_id, "failed", 0, result)
                logger.error(f"Job {job_id} FAILED: {result}")
                
        except Exception as e:
            logger.error(f"Job processing error: {e}")
            if self.current_job:
                self.update_job_status(self.current_job, "failed", 0, {"error": str(e)})
        finally:
            self.current_job = None
            self.send_heartbeat("IDLE")
    
    def _handle_transcribe(self, job_id: str, file_path: str) -> dict:
        """Handle transcription job."""
        if not self.transcribe_service:
            return {"error": "Transcription service not available"}
        
        # Validate media first
        if not validate_media_file(file_path):
            return {"error": "Media validation failed"}
        
        self.update_job_status(job_id, "processing", 30)
        
        # Perform transcription
        sidecar_path = self.transcribe_service.transcribe_to_sidecar(file_path)
        
        if sidecar_path:
            self.update_job_status(job_id, "processing", 80)
            
            # Auto-embed the transcript
            if self.embed_service:
                self.embed_service.embed_document(sidecar_path)
            
            return {"sidecar_path": sidecar_path}
        else:
            return {"error": "Transcription failed"}
    
    def _handle_embed(self, job_id: str, file_path: str) -> dict:
        """Handle embedding job."""
        if not self.embed_service:
            return {"error": "Embedding service not available"}
        
        self.update_job_status(job_id, "processing", 50)
        
        success = self.embed_service.embed_document(file_path)
        
        if success:
            stats = self.embed_service.get_stats()
            return {"embedded": True, "total_documents": stats.get("total_documents", 0)}
        else:
            return {"error": "Embedding failed"}
    
    def _handle_summarize(self, job_id: str, file_path: str) -> dict:
        """Handle summarization job (placeholder)."""
        # TODO: Integrate LLM for summarization
        self.update_job_status(job_id, "processing", 50)
        time.sleep(2)  # Simulate work
        return {"summary": "Summarization not yet implemented", "file": file_path}
    
    def run(self):
        """Main worker loop."""
        logger.info("Worker Loop STARTED. Insomnia Protocol active.")
        
        with InsomniaContext():
            while self.active:
                try:
                    # GameMode check
                    is_gaming, game_name = self._check_gamemode()
                    
                    if is_gaming:
                        if not self.paused:
                            logger.info(f"🎮 GameMode Detected ({game_name}): Pausing...")
                            self.paused = True
                        self.send_heartbeat(f"PAUSED_GAMEMODE ({game_name})")
                        time.sleep(10)
                        continue
                    
                    if self.paused:
                        logger.info("🎮 GameMode Ended: Resuming...")
                        self.paused = False
                    
                    self.send_heartbeat("IDLE")
                    
                    # Poll for jobs (Priority: interactive > batch)
                    job_data = self.redis_client.blpop(
                        ["queue:interactive", "queue:batch"],
                        timeout=5
                    )
                    
                    if job_data:
                        _, job_json = job_data
                        self.process_job(job_json)
                    
                    # Check for stop signal
                    if os.path.exists("STOP_WORKER"):
                        logger.info("Stop signal detected. Shutting down...")
                        self.active = False
                        os.remove("STOP_WORKER")
                
                except redis.ConnectionError:
                    logger.error("Redis connection lost. Retrying in 5s...")
                    time.sleep(5)
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt. Stopping...")
                    self.active = False
        
        logger.info("Worker stopped.")


if __name__ == "__main__":
    node = WorkerNode()
    node.run()
