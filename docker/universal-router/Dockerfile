# Neural Vault Universal Router
# =============================
# Magic Byte Detection + Queue Routing

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY router.py .

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8030/health || exit 1

EXPOSE 8030

CMD ["uvicorn", "router:app", "--host", "0.0.0.0", "--port", "8030"]
