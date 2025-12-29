# Neural Vault WhisperX API
# =========================
# Word-Level Timestamps + Speaker Diarization
#
# Build:
#   docker build -t conductor-whisperx .
#
# Run:
#   docker run --gpus all -p 9000:9000 -e HF_TOKEN=xxx conductor-whisperx

FROM nvidia/cuda:12.1-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3.10-venv \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Install WhisperX (from git for latest version)
RUN pip3 install --no-cache-dir git+https://github.com/m-bain/whisperx.git

# Copy application
COPY server.py .

# Environment defaults
ENV WHISPER_MODEL=large-v3
ENV WHISPER_DEVICE=cuda
ENV WHISPER_COMPUTE_TYPE=float16
ENV WHISPER_BATCH_SIZE=16
ENV HF_TOKEN=""

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# Expose port
EXPOSE 9000

# Run server
CMD ["python3", "server.py"]
