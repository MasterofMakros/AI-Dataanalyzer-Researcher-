# Neural Vault Extraction Workers
# ================================
# Spezialisierte Worker für verschiedene Dateitypen

FROM python:3.11-slim

LABEL maintainer="Neural Vault"
LABEL description="Extraction workers for different file types"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV WORKER_TYPE=documents

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY extraction_worker.py .

CMD ["python", "extraction_worker.py"]
