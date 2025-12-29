# Neural Vault Surya OCR API
# ==========================
# High-Accuracy OCR (97.7%) with Layout Analysis
#
# Build:
#   docker build -t conductor-surya-ocr .
#
# Run:
#   docker run --gpus all -p 9999:8000 conductor-surya-ocr

FROM nvidia/cuda:12.1-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    python3.11-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application
COPY server.py .

# Environment defaults
ENV SURYA_DEVICE=cuda
ENV SURYA_BATCH_SIZE=4
ENV SURYA_LANGS=de,en

# Cache directory for models
ENV HF_HOME=/root/.cache/huggingface

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start_period=180s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run server
CMD ["python3", "server.py"]
