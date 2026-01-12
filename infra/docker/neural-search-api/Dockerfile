# =============================================================================
# Neural Search API - RAG Search with LLM Synthesis
# =============================================================================

FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8040/health || exit 1

EXPOSE 8040

CMD ["uvicorn", "neural_search_api:app", "--host", "0.0.0.0", "--port", "8040"]
