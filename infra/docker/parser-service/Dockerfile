# Neural Vault Parser Service
# Docker Image mit allen Python-Bibliotheken für Datei-Verarbeitung

FROM python:3.11-slim

# System-Abhängigkeiten für OpenEXR + Archive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenexr-dev \
    libimath-dev \
    gcc \
    g++ \
    unrar-free \
    p7zip-full \
    && rm -rf /var/lib/apt/lists/*

# Python-Bibliotheken
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Service-Code
COPY parser_service.py /app/parser_service.py
COPY extended_file_processor.py /app/extended_file_processor.py

WORKDIR /app

# FastAPI Server
EXPOSE 8000
CMD ["uvicorn", "parser_service:app", "--host", "0.0.0.0", "--port", "8000"]
