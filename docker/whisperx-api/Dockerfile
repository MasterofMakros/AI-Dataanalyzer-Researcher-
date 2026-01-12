# Neural Vault WhisperX API
# =========================
# Word-Level Timestamps + Speaker Diarization
# Based on official WhisperX v3.7.4 requirements
#
# Build:
#   docker build -t conductor-whisperx .
#
# Run:
#   docker run --gpus all -p 9000:9000 -e HF_TOKEN=xxx conductor-whisperx

FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Create app directory
WORKDIR /app

# Install WhisperX from PyPI (handles all dependencies correctly)
# This installs torch~=2.8.0, pyannote-audio>=3.3.2, etc.
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir whisperx

# Install additional API dependencies
RUN pip3 install --no-cache-dir \
    fastapi==0.115.6 \
    uvicorn[standard]==0.34.0 \
    python-multipart==0.0.18

# Copy application
COPY server.py .

# Environment defaults
ENV WHISPER_MODEL=large-v3
ENV WHISPER_DEVICE=cuda
ENV WHISPER_COMPUTE_TYPE=float16
ENV WHISPER_BATCH_SIZE=16
ENV HF_TOKEN=""

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# Expose port
EXPOSE 9000

# Run server
CMD ["python3", "server.py"]
