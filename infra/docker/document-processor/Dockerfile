# Neural Vault Document Processor
# ================================
# Unified GPU Service: Docling + Surya OCR + GLiNER
#
# Benchmark Basis:
# - Docling: 97.9% Table Accuracy (vs Tika 75%)
# - Surya OCR: 97.7% Accuracy (vs Tesseract 87%)
# - GLiNER: Zero-shot NER/PII Detection
#
# Build:
#   docker build -t conductor-document-processor .
#
# Run:
#   docker run --gpus all -p 8005:8000 conductor-document-processor

FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    python3.11-venv \
    python3.11-dev \
    build-essential \
    git \
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
COPY main.py .

# Environment defaults
ENV PROCESSOR_DEVICE=cuda
ENV GLINER_MODEL=urchade/gliner_small-v2.1
ENV EMBED_MODEL=Alibaba-NLP/gte-Qwen3-Embedding-0.6B
ENV SURYA_BATCH_SIZE=4
ENV SURYA_LANGS=de,en
ENV LANCEDB_PATH=/data/lancedb

# Cache directories for models
ENV HF_HOME=/root/.cache/huggingface
ENV TORCH_HOME=/root/.cache/torch

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run server
CMD ["python3", "main.py"]
