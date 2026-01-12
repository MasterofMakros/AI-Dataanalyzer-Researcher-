"""
Service Pattern (FastAPI)
=========================
Reference implementation for a microservice in this repo.
Use this structure for all new API services.
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# 1. Configuration (Environment Variables)
# NOTE: Use defaults compatible with Docker Compose
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# 2. Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("service_pattern")

# 3. Data Models (Pydantic)
class RequestModel(BaseModel):
    query: str = Field(..., min_length=3, description="Input query")
    options: Optional[Dict[str, Any]] = None

class ResponseModel(BaseModel):
    result: str
    status: str

# 4. App Initialization
app = FastAPI(
    title="Service Pattern",
    description="Reference implementation",
    version="1.0.0"
)

# 5. Core Endpoints
@app.get("/health")
async def health_check():
    """Standard Docker Healthcheck."""
    return {"status": "healthy", "service": "service_pattern"}

@app.post("/process", response_model=ResponseModel)
async def process_data(request: RequestModel):
    """Business logic endpoint."""
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Simulation of logic
        if request.query == "error":
            raise ValueError("Simulated business logic error")
            
        return ResponseModel(
            result=f"Processed: {request.query}",
            status="success"
        )
    except ValueError as e:
        logger.error(f"Logic Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("System Error")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 6. Entry Point (Dev Mode)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
