# Neural Vault Orchestrator
# =========================
# Intelligence-Grade Job Distribution

FROM python:3.11-slim

LABEL maintainer="Neural Vault"
LABEL description="Queue-based job orchestration with priority scoring"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY orchestrator.py .

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8020/health || exit 1

EXPOSE 8020

CMD ["uvicorn", "orchestrator:app", "--host", "0.0.0.0", "--port", "8020"]
