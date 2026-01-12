import time
import os
import redis
import json
import logging
import docker
import requests
from gamemode import check_gamemode

# Configuration
REDIS_HOST = "192.168.1.254"
REDIS_PORT = 6379
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")  # Loaded from env
QUEUE_NAME = "ai_jobs"
DOCKER_COMPOSE_FILE = "docker-compose.gpu.yml"
PROJECT_NAME = "conductor-gpu"

# Init Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Guardian")

# Init Docker Client
try:
    docker_client = docker.from_env()
except Exception as e:
    logger.error(f"Failed to connect to Docker: {e}")
    exit(1)

# Init Redis
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
    r.ping()
    logger.info(f"Connected to Redis at {REDIS_HOST}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    exit(1)

def is_ai_stack_running():
    """Check if our GPU containers are up."""
    containers = docker_client.containers.list(filters={"name": "conductor-ollama"})
    return len(containers) > 0

def start_ai_stack():
    """Spin up the GPU stack."""
    if is_ai_stack_running():
        return
    logger.info("🚀 Starting AI Stack (GPU)...")
    # In a real scenario, we might use subprocess to call 'docker compose up' 
    # to ensure all networks/volumes are handled correctly by compose.
    os.system(f"docker compose -f {DOCKER_COMPOSE_FILE} up -d")
    # Wait for health check (simplified)
    time.sleep(5) 

def stop_ai_stack():
    """Spin down to save VRAM/Electricity."""
    if not is_ai_stack_running():
        return
    logger.info("💤 Stopping AI Stack...")
    os.system(f"docker compose -f {DOCKER_COMPOSE_FILE} stop")

def process_job(job_data):
    """
    Execute the job. 
    In v1, this calls the local API that we just started.
    """
    job = json.loads(job_data)
    job_type = job.get("type")
    logger.info(f"Processing Job: {job_type} - ID: {job.get('id')}")

    try:
        if job_type == "transcribe":
            # 1. Download File from Nextcloud (URL provided in job)
            # 2. Call Whisper API
            # 3. Post result back to n8n webhook
            pass # Implementation TODO
            
        elif job_type == "generate":
            # Call Ollama API
            pass # Implementation TODO
            
        logger.info(f"✅ Job {job.get('id')} completed.")
        
    except Exception as e:
        logger.error(f"❌ Job failed: {e}")

def loop():
    logger.info("🛡️ Guardian Active. Polling for work...")
    
    while True:
        # 1. Check GameMode
        is_gaming, game_name = check_gamemode()
        if is_gaming:
            logger.warning(f"🎮 Gaming detected ({game_name}). Pausing Guardian.")
            stop_ai_stack() # Kill Docker to free GPU for Game
            time.sleep(30) # Check again in 30s
            continue

        # 2. Check Redis Queue (Blocking Pop with 5s timeout)
        # This acts as our "Pulse" - if no work, we just wait.
        try:
            # blpop returns tuple (queue_name, data) or None
            job = r.blpop(QUEUE_NAME, timeout=5)
            
            if job:
                queue, data = job
                logger.info("⚡ Job received!")
                
                # Spark up the engine
                start_ai_stack()
                
                # Do the work
                process_job(data)
                
            else:
                # Idle... maybe stop stack after X minutes of idle?
                # For now, keep it simple.
                pass
                
        except redis.ConnectionError:
            logger.error("Lost connection to Redis. Retrying in 10s...")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    loop()
