FROM python:3.11-slim

# Build argument for CUDA support
ARG CUDA_ENABLED=false

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install PyTorch with CUDA if enabled
RUN if [ "$CUDA_ENABLED" = "true" ]; then \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121; \
    fi

# Copy application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV CONDUCTOR_API_URL=http://conductor-api:8000
ENV REDIS_HOST=conductor-redis
ENV REDIS_PORT=6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import redis; r=redis.Redis(host='${REDIS_HOST}', port=6379); r.ping()" || exit 1

# Run worker
CMD ["python", "worker.py"]
